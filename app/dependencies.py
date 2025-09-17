from sqlalchemy.orm import Session, sessionmaker # cria sessões para interagir com o banco
from fastapi import Depends, HTTPException # cria dependências e exceções HTTP
from jose import jwt, JWTError # manipula JSON Web Tokens
from app.config import kEY_CRYPT, ALGORITHM, oauth2_schema # importa configurações de segurança

"""
    Realiza toda a configuração da conexão com o banco de dados e retorna:
    - engine: objeto de conexão
    - SessionLocal: função para criar sessões
    - Base: classe base para os modelos ORM

"""
# Configuração da conexão com o banco de dados
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine # cria a conexão com o banco de dados
from sqlalchemy.orm import sessionmaker, declarative_base # cria sessões para interagir com o banco e define a classe base para os modelos

load_dotenv()
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()



# Obter uma sessão do banco de dados
def pegar_sessao():
    try:
        session = SessionLocal()
        yield session
    finally: 
        session.close()

# Verificar o token JWT e obter o usuário autenticado
def verificar_token(token: str = Depends(oauth2_schema), session: Session = Depends(pegar_sessao)):
    from app.models import Usuario
    try:
        dic_info = jwt.decode(token, kEY_CRYPT, ALGORITHM) # decodifica o token para extrair as informações
        id_usuario = int(dic_info.get("sub")) # extrai o id do usuário do token
    except JWTError:
        raise HTTPException(status_code=401, detail="Acesso negado, verifique a validade do token")
    usuario = session.query(Usuario).filter(Usuario.id==id_usuario).first() # busca o usuário na sessão
    if not usuario:
        raise HTTPException(status_code=401, detail="Acesso inválido")
    return usuario
