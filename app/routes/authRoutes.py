from fastapi import APIRouter, Depends, HTTPException
from app.services.usuario import criar_usuario, atualizar_usuario, buscar_usuario_por_email
from sqlalchemy.orm import Session
from app.models import Usuario
from app.dependencies import pegar_sessao, verificar_token
from app.config import bcrypt_context, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, kEY_CRYPT
from app.schemas import UsuarioBase, LoginSchema, RecuperarSenhaSchema
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone # datetime para lidar com datas e horas | timedelta para manipular durações de tempo | timezone para lidar com fusos horários

authRouter = APIRouter(prefix="/auth", tags=["auth"])

# Cadastrar usuário
@authRouter.post("/cadastro")
async def cadastro(usuario_schema: UsuarioBase, session: Session = Depends(pegar_sessao)): # passa como parametro os dados que o usuário tem que inserir ao acessar a rota e a sessão do banco de dados
    usuario = session.query(Usuario).filter(Usuario.email == usuario_schema.email).first() # verifica se o email já existe no banco de dados. (first pega o primeiro resultado que encontrar, se encontrar algum resultado, significa que o email já existe)
    if usuario: 
        raise HTTPException(status_code=401, detail="Email já cadastrado") # se ja existir um usuario com esse email, retorna um erro
    else:
        usuario_schema.senha = bcrypt_context.hash(usuario_schema.senha) # criptografa a senha do usuário
        novo_usuario = criar_usuario(session, usuario_schema) # se não existir, cria o usuário
        return {"message": f"Usuário cadastrado com sucesso {novo_usuario.nome}"}

# Login de usuário
@authRouter.post("/login")
async def login(login_schema: LoginSchema, session: Session = Depends(pegar_sessao)):
    usuario=autenticar_usuario(login_schema.email, login_schema.senha, session)
    if not usuario:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")
    else:
        access_token = criar_token(usuario.id) # cria o token de acesso
        refresh_token = criar_token(usuario.id, duracao_token=timedelta(days=7)) # cria o token de atualização (30 dias)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"
            } 

# Usar o refresh token para obter um novo access token
@authRouter.get("/refresh")
async def usar_refresh_token(usuario: Usuario = Depends(verificar_token)):
    access_token = criar_token(usuario.id)
    return {
        "access_token": access_token,
        "token_type": "Bearer"
        }

# Recuperar senha
@authRouter.put("/recuperar-senha")
async def recuperar_senha(dados: RecuperarSenhaSchema, session: Session = Depends(pegar_sessao)):
    usuario = buscar_usuario_por_email(dados.email, session)
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    usuario.senha = bcrypt_context.hash(dados.nova_senha) # atualiza a senha do usuário com a nova senha criptografada
    atualizar_usuario(session, usuario)
    return {"message": "Senha atualizada com sucesso"}

# ======================== FUNÇÕES AUXILIARES =======================

# Para refresh
def criar_token(id_usuario, duracao_token = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)):
    data_expiracao = datetime.now(timezone.utc) + duracao_token  # define o tempo de expiração do token (tempo em minutos a partir do momento atual definido pelo fuso horário padrão (utc))
    dic_info = {
        "sub": str(id_usuario), # sub = subject (assunto) --> identifica o usuário
        "exp": int(data_expiracao.timestamp()) # exp = expiration (expiração) --> define o tempo de expiração do token
    }
    jwt_codificado = jwt.encode(dic_info,kEY_CRYPT, ALGORITHM) # codifica o token com a chave de criptografia e o algoritmo definido
    return jwt_codificado

# Para login
def autenticar_usuario(email, senha, session):
    usuario = session.query(Usuario).filter(Usuario.email == email).first() # Cria uma sessão para verificar na tabela USUARIO se o e-mail corresponde ao que foi inserido no schema  
    if not usuario:
        return False
    elif not bcrypt_context.verify(senha, usuario.senha):
        return False
    return usuario 