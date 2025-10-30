from fastapi import APIRouter, Depends, HTTPException, Request, Response # cria dependências e exceções HTTP
from fastapi.security import OAuth2PasswordRequestForm # esquema de segurança para autenticação
from app.services.usuario import criar_usuario # serviços relacionados ao usuário
from sqlalchemy.orm import Session # cria sessões com o banco de dados
from app.models import Usuario, CodigoAutenticacao, Carreira, Curso
from app.dependencies import pegar_sessao, verificar_token # pegar a sessão do banco de dados e verificar o token
from app.config import bcrypt_context, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, kEY_CRYPT # configuração de criptografia e autenticação
from app.schemas import UsuarioBase, LoginSchema, ConfirmarNovaSenhaSchema, SolicitarCodigoSchema # schemas para validação de dados
from jose import JWTError, jwt # trabalhar com JSON Web Token (JWT)
from random import randint # gerar números aleatórios
from datetime import datetime, timedelta, timezone # lidar com datas e horas | manipular durações de tempo | lidar com fusos horários
from dotenv import load_dotenv # carregar as variáveis de ambiente
import os # interagir com o sistema operacional
import resend # enviar emails

load_dotenv()
PRODUCTION = os.getenv("ENV") == "production" or os.getenv("PRODUCTION") == "1"

# Inicializa o router
authRouter = APIRouter(prefix="/auth", tags=["auth"])

# Cadastrar usuário
@authRouter.post("/cadastro")
async def cadastro(usuario_schema: UsuarioBase, session: Session = Depends(pegar_sessao)): # passa como parametro os dados que o usuário tem que inserir ao acessar a rota e a sessão do banco de dados
    usuario = session.query(Usuario).filter(Usuario.email == usuario_schema.email).first() # verifica se o email já existe no banco de dados. (first pega o primeiro resultado que encontrar, se encontrar algum resultado, significa que o email já existe)
    if usuario:
        raise HTTPException(status_code=400, detail="Email já cadastrado") # se ja existir um usuario com esse email, retorna um erro

    # Normaliza 0 -> None para evitar violação de FK
    if usuario_schema.carreira_id == 0:
        usuario_schema.carreira_id = None
    if usuario_schema.curso_id == 0:
        usuario_schema.curso_id = None

    # Se não é admin, exige carreira e curso válidos
    if not usuario_schema.admin:
        if usuario_schema.carreira_id is None or usuario_schema.curso_id is None:
            raise HTTPException(status_code=400, detail="carreira_id e curso_id são obrigatórios para usuários não-admin")
        if session.get(Carreira, usuario_schema.carreira_id) is None:
            raise HTTPException(status_code=400, detail="Carreira inexistente")
        if session.get(Curso, usuario_schema.curso_id) is None:
            raise HTTPException(status_code=400, detail="Curso inexistente")

    usuario_schema.senha = bcrypt_context.hash(usuario_schema.senha) # criptografa a senha do usuário
    novo_usuario = criar_usuario(session, usuario_schema) # se não existir, cria o usuário
    return {"message": f"Usuário cadastrado com sucesso {novo_usuario.nome}"}

# Login de usuário
@authRouter.post("/login")
async def login(login_schema: LoginSchema, session: Session = Depends(pegar_sessao), response: Response = None):
    usuario=autenticar_usuario(login_schema.email, login_schema.senha, session) # autentica o usuário
    if not usuario:
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos")
    else:
        access_token = criar_token(usuario.id) # cria o token de acesso
        # cria refresh token e seta em cookie HttpOnly (browser enviará automaticamente em requests subsequentes)
        refresh_token = criar_token(usuario.id, duracao_token=timedelta(days=7)) # 7 dias

        # set cookie seguro para produção (SameSite=None para cross-site, secure=True requer HTTPS)
        if response is not None:
            # max_age em segundos
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=PRODUCTION,
                samesite=("None" if PRODUCTION else "Lax"),
                max_age=7*24*3600,
                path="/",
            )

        # retorna apenas o access token; refresh token é enviado em cookie HttpOnly
        return {
            "access_token": access_token,
            "token_type": "Bearer"
        }

# Usar o refresh token para obter um novo access token - AUTENTICADA
@authRouter.post("/refresh")
async def usar_refresh_token(request: Request, response: Response, session: Session = Depends(pegar_sessao)):
    # Lê refresh token de cookie HttpOnly
    refresh = request.cookies.get("refresh_token")
    if not refresh:
        raise HTTPException(status_code=401, detail="Sem refresh token")

    try:
        payload = jwt.decode(refresh, kEY_CRYPT, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    usuario = session.get(Usuario, user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # cria novo access token
    access_token = criar_token(usuario.id)

    # opcional: rotacionar refresh token
    try:
        new_refresh = criar_token(usuario.id, duracao_token=timedelta(days=7))
        response.set_cookie(
            key="refresh_token",
            value=new_refresh,
            httponly=True,
            secure=PRODUCTION,
            samesite=("None" if PRODUCTION else "Lax"),
            max_age=7*24*3600,
            path="/",
        )
    except Exception:
        # se a rotação falhar, não impede a emissão do access token
        pass

    return {"access_token": access_token, "token_type": "Bearer"}


# Logout - remove refresh cookie
@authRouter.post("/logout")
async def logout(response: Response):
    # Deleta o cookie de refresh no caminho raiz
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logout realizado"}

# Solicitar código de verificação por email (motivo: recuperacao_senha)
@authRouter.post("/solicitar-codigo/recuperar-senha")
async def solicitar_codigo_recuperar(payload: SolicitarCodigoSchema, session: Session = Depends(pegar_sessao)):
    usuario = session.query(Usuario).filter(Usuario.email == payload.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    _gerar_codigo(session, usuario, "recuperacao_senha")
    return {"message": "Código enviado para recuperação de senha"}

# Confirmar código + recuperar senha
@authRouter.post("/recuperar-senha")  # mantido nome para compatibilidade de frontend
async def confirmar_nova_senha(nova_senha: ConfirmarNovaSenhaSchema, session: Session = Depends(pegar_sessao)):
    # Busca último código válido para motivos de senha
    usuario = session.query(Usuario).filter(Usuario.email == nova_senha.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    rec = (
        session.query(CodigoAutenticacao)
        .filter(CodigoAutenticacao.usuario_id == usuario.id, CodigoAutenticacao.motivo.in_(["recuperacao_senha"])) # filtra por motivo de recuperação de senha
        .order_by(CodigoAutenticacao.id.desc())
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Nenhum código de verificação gerado para este email")
    if rec.codigo_expira_em < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Código expirado")
    if not bcrypt_context.verify(nova_senha.codigo, rec.codigo_recuperacao):
        raise HTTPException(status_code=400, detail="Código inválido")

    usuario.senha = bcrypt_context.hash(nova_senha.nova_senha)
    session.delete(rec) # remove o código usado
    session.commit()
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

# Para enviar o email com o código
def enviar_email(destinatario: str, codigo: str):
    assunto = "Código"
    corpo = f"Seu código é: {codigo}"
    resend.api_key = os.getenv("RESEND_API_KEY")
    remetente = os.getenv("EMAIL_FROM")

    try:
        resp = resend.Emails.send({
            "from": remetente,
            "to": [destinatario],
            "subject": assunto,
            "text": corpo,
        })
        # validação de sucesso do envio quando o e-mail foi aceito pela Resend
        if not resp or not resp.get("id"):
            raise RuntimeError(str(resp))
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao enviar email: {e}")

# Gera e envia o código de verificação por email e envia o email
def _gerar_codigo(session: Session, usuario: Usuario, motivo: str):
    codigo = str(randint(100000, 999999))
    rec = CodigoAutenticacao(
        usuario_id=usuario.id,
        codigo_recuperacao=bcrypt_context.hash(codigo),
        codigo_expira_em=datetime.utcnow() + timedelta(minutes=10),
        motivo=motivo
    )
    session.add(rec)
    session.commit()
    enviar_email(usuario.email, codigo)
