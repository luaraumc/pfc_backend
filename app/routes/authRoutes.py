from fastapi import APIRouter, Depends, HTTPException # cria dependências e exceções HTTP
from fastapi.security import OAuth2PasswordRequestForm # esquema de segurança para autenticação
from app.services.usuario import criar_usuario # serviços relacionados ao usuário
from sqlalchemy.orm import Session # cria sessões com o banco de dados
from app.models import Usuario, RecuperacaoSenha # modelo de tabela definido no arquivo models.py
from app.dependencies import pegar_sessao, verificar_token # pegar a sessão do banco de dados e verificar o token
from app.config import bcrypt_context, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, kEY_CRYPT # configuração de criptografia e autenticação
from app.schemas import UsuarioBase, LoginSchema, ConfirmarNovaSenhaSchema # schemas para validação de dados
from jose import JWTError, jwt # trabalhar com JSON Web Token (JWT)
import smtplib # enviar emails
from email.mime.text import MIMEText # formatar o conteúdo do email
from random import randint # gerar números aleatórios
from datetime import datetime, timedelta, timezone # lidar com datas e horas | manipular durações de tempo | lidar com fusos horários
from dotenv import load_dotenv # carregar as variáveis de ambiente
import os # interagir com o sistema operacional

load_dotenv()

# Inicializa o router
authRouter = APIRouter(prefix="/auth", tags=["auth"])

# Cadastrar usuário
@authRouter.post("/cadastro")
async def cadastro(usuario_schema: UsuarioBase, session: Session = Depends(pegar_sessao)): # passa como parametro os dados que o usuário tem que inserir ao acessar a rota e a sessão do banco de dados
    usuario = session.query(Usuario).filter(Usuario.email == usuario_schema.email).first() # verifica se o email já existe no banco de dados. (first pega o primeiro resultado que encontrar, se encontrar algum resultado, significa que o email já existe)
    if usuario: 
        raise HTTPException(status_code=400, detail="Email já cadastrado") # se ja existir um usuario com esse email, retorna um erro
    else:
        usuario_schema.senha = bcrypt_context.hash(usuario_schema.senha) # criptografa a senha do usuário
        novo_usuario = criar_usuario(session, usuario_schema) # se não existir, cria o usuário
        return {"message": f"Usuário cadastrado com sucesso {novo_usuario.nome}"}

# Login de usuário
@authRouter.post("/login")
async def login(login_schema: LoginSchema, session: Session = Depends(pegar_sessao)):
    usuario=autenticar_usuario(login_schema.email, login_schema.senha, session) # autentica o usuário
    if not usuario:
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")
    else:
        access_token = criar_token(usuario.id) # cria o token de acesso
        refresh_token = criar_token(usuario.id, duracao_token=timedelta(days=7)) # cria o token de atualização (7 dias)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"
            }
    
# Login de usuário para o fastapi docs
@authRouter.post("/login-form")
async def login_form(dados_formulario: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(pegar_sessao)):
    usuario=autenticar_usuario(dados_formulario.username, dados_formulario.password, session) # autentica o usuário
    if not usuario:
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")
    else:
        access_token = criar_token(usuario.id) # cria o token de acesso
        return {
            "access_token": access_token,
            "token_type": "Bearer"
            }


# Usar o refresh token para obter um novo access token - AUTENTICADA
@authRouter.get("/refresh")
async def usar_refresh_token(usuario: Usuario = Depends(verificar_token)): # verifica o token de acesso
    access_token = criar_token(usuario.id) # cria um novo token de acesso
    return {
        "access_token": access_token,
        "token_type": "Bearer"
        }

# Recuperar senha 1/2 - envia email com código, cria registro na tabela de recuperação
@authRouter.post("/recuperar-senha")
async def recuperar_senha(email: str, session: Session = Depends(pegar_sessao)): # recebe o email do usuário e a sessão do banco de dados
    usuario = session.query(Usuario).filter(Usuario.email == email).first() # verifica se o email existe no banco de dados
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    codigo = str(randint(100000, 999999)) # gera um código de 6 dígitos
    hash_codigo = bcrypt_context.hash(codigo) # criptografa o código
    expira_em = datetime.utcnow() + timedelta(minutes=10) # define o tempo de expiração do código (10 minutos a partir do momento atual)

    # cria o registro na tabela de recuperação de senha
    rec = RecuperacaoSenha( 
        usuario_id=usuario.id,
        email=usuario.email,
        codigo_recuperacao=hash_codigo,
        codigo_expira_em=expira_em
    )

    session.add(rec) # adiciona o registro na sessão
    session.commit() # salva o registro no banco de dados
    enviar_email(usuario.email, codigo) # envia o email com o código
    return {"message": "Código enviado para o e-mail"}

# Recuperar senha 2/2 - confirma o código e atualiza a senha
@authRouter.post("/recuperar-senha/confirmar")
async def confirmar_nova_senha(nova_senha: ConfirmarNovaSenhaSchema, session: Session = Depends(pegar_sessao)): # recebe o email, o código e a nova senha do usuário e a sessão do banco de dados
    rec = session.query(RecuperacaoSenha).filter(RecuperacaoSenha.email == nova_senha.email).order_by(RecuperacaoSenha.id.desc()).first() # busca o registro mais recente na tabela de recuperação de senha para o email fornecido
    if not rec:
        raise HTTPException(status_code=404, detail="Nenhum pedido de recuperação encontrado para este email") # se não encontrar nenhum registro, retorna um erro
    if rec.codigo_expira_em < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Código expirado") # se o código expirou, retorna um erro
    if not bcrypt_context.verify(nova_senha.codigo, rec.codigo_recuperacao):
        raise HTTPException(status_code=400, detail="Código inválido") # se o código não for válido, retorna um erro

    usuario = session.query(Usuario).filter(Usuario.email == nova_senha.email).first() # busca o usuário pelo email
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado") 

    usuario.senha = bcrypt_context.hash(nova_senha.nova_senha) # atualiza a senha do usuário
    session.commit() # salva a nova senha no banco de dados
    return {"detail": "Senha atualizada com sucesso"}

# ======================== FUNÇÕES AUXILIARES =======================

# Para refresh
def criar_token(id_usuario, duracao_token = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)):
    data_expiracao = datetime.now(timezone.utc) + duracao_token  # define o tempo de expiração do token (tempo em minutos a partir do momento atual definido pelo fuso horário padrão (utc))
    dic_informacoes = {
        "sub": str(id_usuario), # sub = subject (assunto) --> identifica o usuário
        "exp": data_expiracao # exp = expiration (expiração) --> define o tempo de expiração do token
    }
    jwt_codificado = jwt.encode(dic_informacoes,kEY_CRYPT, ALGORITHM) # codifica o token com a chave de criptografia e o algoritmo definido
    return jwt_codificado

# Para login
def autenticar_usuario(email, senha, session):
    usuario = session.query(Usuario).filter(Usuario.email == email).first() # cria uma sessão para verificar na tabela usuario se o e-mail corresponde ao que foi inserido no schema  
    if not usuario:
        return False
    elif not bcrypt_context.verify(senha, usuario.senha): # compara a senha inserida com a senha criptografada no banco
        return False
    return usuario 

# Para recuperar senha
def enviar_email(destinatario, codigo):
    # configurações do email
    remetente = os.getenv("EMAIL_REMETENTE")
    senha = os.getenv("EMAIL_SENHA")
    assunto = "Código de recuperação de senha"
    corpo = f"Seu código de recuperação é: {codigo}"

    # formata o email
    msg = MIMEText(corpo)
    msg["Subject"] = assunto
    msg["From"] = remetente
    msg["To"] = destinatario

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp: # conecta ao servidor do Gmail
        smtp.login(remetente, senha) # faz login com o email e a senha do remetente
        smtp.sendmail(remetente, destinatario, msg.as_string()) # envia o email
