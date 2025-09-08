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