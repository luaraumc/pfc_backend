from fastapi import APIRouter, Depends, HTTPException, Request, Response, Body 
from app.services.usuario import criar_usuario 
from sqlalchemy.orm import Session
from app.models.usuarioModels import Usuario
from app.models.codigoAutenticacaoModels import CodigoAutenticacao
from app.models.carreiraModels import Carreira
from app.dependencies import pegar_sessao
from app.config import bcrypt_context, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, KEY_CRYPT 
from app.schemas.authSchemas import LoginSchema, ConfirmarNovaSenhaSchema, SolicitarCodigoSchema 
from app.schemas.usuarioSchemas import UsuarioBase, UsuarioOut
from jose import JWTError, jwt 
from random import randint 
from datetime import datetime, timedelta, timezone 
from dotenv import load_dotenv 
import os 
import resend 
from pydantic import ValidationError
from app.utils.errors import raise_validation_http_exception


load_dotenv()


authRouter = APIRouter(prefix="/auth", tags=["auth"])


@authRouter.post("/cadastro")
async def cadastro(usuario_payload: UsuarioBase, session: Session = Depends(pegar_sessao)):
    """Cadastra um novo usuário no sistema."""
    try:
        usuario_schema = UsuarioBase.model_validate(usuario_payload)
    except ValidationError as e:
        raise_validation_http_exception(e)

    usuario = session.query(Usuario).filter(Usuario.email == usuario_schema.email).first()
    if usuario:
        raise HTTPException(status_code=400, detail="Email já cadastrado.")

    if usuario_schema.carreira_id == 0:
        usuario_schema.carreira_id = None
    if usuario_schema.curso_id == 0:
        usuario_schema.curso_id = None

    usuario_schema.senha = bcrypt_context.hash(usuario_schema.senha) 
    criar_usuario(session, usuario_schema) 
    return {"message": f"Usuário cadastrado com sucesso! Redirecionando..."}


@authRouter.post("/login")
async def login(login_payload: LoginSchema, session: Session = Depends(pegar_sessao), response: Response = None):
    """Autentica o usuário e retorna apenas o access token; refresh token é enviado em cookie HttpOnly."""
    try:
        login_schema = LoginSchema.model_validate(login_payload)
    except ValidationError as e:
        raise_validation_http_exception(e)

    usuario=autenticar_usuario(login_schema.email, login_schema.senha, session) 
    if not usuario:
        raise HTTPException(status_code=400, detail="E-mail ou senha incorretos.")
    else:
        access_token = criar_token(usuario.id) 

        # cria refresh token e seta em cookie HttpOnly (navegador enviará automaticamente em requests subsequentes)
        refresh_token = criar_token(usuario.id, duracao_token=timedelta(days=7))

        if response is not None:
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite="None",
                max_age=7*24*3600,
                path="/",
            )

        return {
            "access_token": access_token,
            "token_type": "Bearer"
        }


@authRouter.post("/refresh")
async def usar_refresh_token(request: Request, response: Response, session: Session = Depends(pegar_sessao)):
    """Usa o refresh token (de cookie HttpOnly) para obter um novo access token."""

    refresh = request.cookies.get("refresh_token")
    if not refresh:
        raise HTTPException(status_code=401, detail="Sem refresh token")
    
    try:
        payload = jwt.decode(refresh, KEY_CRYPT, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    usuario = session.get(Usuario, user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    
    access_token = criar_token(usuario.id)
    
    try:
        new_refresh = criar_token(usuario.id, duracao_token=timedelta(days=7))

        # atualiza cookie de refresh para cross-site
        response.set_cookie(
            key="refresh_token",
            value=new_refresh,
            httponly=True,
            secure=True,
            samesite="None",
            max_age=7*24*3600,
            path="/",
        )
    except Exception:
        pass

    return {"access_token": access_token, "token_type": "Bearer"}


@authRouter.post("/logout")
async def logout(response: Response):
    """Realiza logout removendo o cookie de refresh token."""
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logout realizado"}


@authRouter.post("/solicitar-codigo/recuperar-senha")
async def solicitar_codigo_recuperar(payload: SolicitarCodigoSchema, session: Session = Depends(pegar_sessao)):
    """Solicita um código de verificação para recuperação de senha."""
    usuario = session.query(Usuario).filter(Usuario.email == payload.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    _gerar_codigo(session, usuario, "recuperacao_senha")
    return {"message": "Código enviado para recuperação de senha."}


@authRouter.post("/recuperar-senha") 
async def confirmar_nova_senha(nova_senha: ConfirmarNovaSenhaSchema, session: Session = Depends(pegar_sessao)):
    """Confirma o código de verificação e atualiza a senha do usuário."""

    usuario = session.query(Usuario).filter(Usuario.email == nova_senha.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    rec = (
        session.query(CodigoAutenticacao)
        .filter(CodigoAutenticacao.usuario_id == usuario.id, CodigoAutenticacao.motivo.in_(["recuperacao_senha"])) 
        .order_by(CodigoAutenticacao.id.desc())
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Nenhum código de verificação gerado para este email.")
    if rec.codigo_expira_em < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Código expirado.")
    if not bcrypt_context.verify(nova_senha.codigo, rec.codigo_recuperacao):
        raise HTTPException(status_code=400, detail="Código inválido.")

    usuario.senha = bcrypt_context.hash(nova_senha.nova_senha)
    session.delete(rec)
    session.commit()
    return {"detail": "Senha atualizada com sucesso."}


# ======================== FUNÇÕES AUXILIARES =======================


def criar_token(id_usuario, duracao_token = timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)):
    """Cria um token JWT para o usuário com tempo de expiração definido."""
    data_expiracao = datetime.now(timezone.utc) + duracao_token 
    dic_informacoes = {
        "sub": str(id_usuario),
        "exp": data_expiracao 
    }
    jwt_codificado = jwt.encode(dic_informacoes,KEY_CRYPT, ALGORITHM) 
    return jwt_codificado


def autenticar_usuario(email, senha, session):
    """Verifica se o email e senha correspondem."""
    usuario = session.query(Usuario).filter(Usuario.email == email).first() 
    if not usuario:
        return False
    elif not bcrypt_context.verify(senha, usuario.senha):
        return False
    return usuario


def enviar_email(destinatario: str, codigo: str):
    """Envia um email com o código de verificação usando Resend."""
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

        if not resp or not resp.get("id"):
            raise RuntimeError(str(resp))
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao enviar email: {e}")


def _gerar_codigo(session: Session, usuario: Usuario, motivo: str):
    """Gera um código de verificação, salva no banco e envia por email."""
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
