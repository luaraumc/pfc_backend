# CRUD DE USUARIO USANDO SQLALCHEMY

# CRUD DE CURSO USANDO SQLALCHEMY

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
# create_engine: cria a conexão com o banco de dados
# Column, Integer, String, Text, DateTime: definem os tipos e colunas das tabelas

from sqlalchemy.ext.declarative import declarative_base
# declarative_base: base para a criação dos modelos ORM

from sqlalchemy.orm import sessionmaker
# sessionmaker: cria sessões para manipular o banco

from sqlalchemy.sql import func
# func permite usar funções SQL nativas, como NOW() para datetime

import os
# acessa variáveis de ambiente do sistema

# Configuração da conexão
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()