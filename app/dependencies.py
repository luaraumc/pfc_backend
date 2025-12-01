from sqlalchemy.orm import Session, sessionmaker 
from fastapi import Depends, HTTPException 
from jose import jwt, JWTError
from app.config import KEY_CRYPT, ALGORITHM, oauth2_schema 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Any
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def pegar_sessao():
    """Dependência para obter uma sessão do banco de dados"""
    try:
        session = SessionLocal()
        yield session
    finally: 
        session.close()

# Verificar o token JWT e obter o usuário autenticado
def verificar_token(token: str = Depends(oauth2_schema), session: Session = Depends(pegar_sessao)):
    """Verifica o token JWT e retorna o usuário autenticado ou levanta uma exceção HTTP 401"""
    from app.models.usuarioModels import Usuario
    try:
        dic_info = jwt.decode(token, KEY_CRYPT, ALGORITHM) # decodifica o token para extrair as informações
        id_usuario = int(dic_info.get("sub"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Acesso negado, verifique a validade do token")
    usuario = session.query(Usuario).filter(Usuario.id==id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Acesso inválido")
    return usuario

# Verifica se o usuário autenticado é um administrador
def requer_admin(usuario: Any = Depends(verificar_token)):
    """Verifica se o usuário autenticado é um administrador, levantando exceção HTTP 403 se não for"""
    is_admin = getattr(usuario, "admin", None)
    if is_admin is None and isinstance(usuario, dict):
        is_admin = usuario.get("admin")
    if not is_admin:
        raise HTTPException(status_code=403, detail="Acesso restrito")
    return usuario
