from sqlalchemy.orm import Session, sessionmaker
from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from app.config import kEY_CRYPT, ALGORITHM

"""
    Realiza toda a configuração da conexão com o banco de dados e retorna:
    - engine: objeto de conexão
    - SessionLocal: função para criar sessões
    - Base: classe base para os modelos ORM
"""

def setup_database():
    import os
    from dotenv import load_dotenv
    from sqlalchemy import create_engine # cria a conexão com o banco de dados
    from sqlalchemy.orm import sessionmaker, declarative_base # cria sessões para interagir com o banco e define a classe base para os modelos

    load_dotenv()
    DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    return engine, SessionLocal, Base

engine, SessionLocal, Base = setup_database()

def pegar_sessao():
    try:
        session = SessionLocal()
        yield session
    finally: 
        session.close()

def verificar_token(token, session: Session = Depends(pegar_sessao)):
    from app.models import Usuario
    try:
        dic_info = jwt.decode(token, kEY_CRYPT, ALGORITHM)
        id_usuario = dic_info.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Acesso negado, verifique a validade do token")
    # verificar se o token é válido
    # extrair o id do usuário do token
    usuario = session.query(Usuario).filter(Usuario.id==id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Acesso inválido")
    return usuario
