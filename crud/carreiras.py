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

engine = create_engine(DATABASE_URL)  # Cria o objeto de conexão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # Gera sessões para executar operações
Base = declarative_base()  # Base para definição dos modelos ORM (tabelas)

# Modelo tabela "carreiras"
class Carreira(Base):
	__tablename__ = 'carreiras'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), nullable=False)
	descricao = Column(Text, nullable=False)
	criado_em = Column(DateTime, server_default=func.now())
	atualizado_em = Column(DateTime, server_default=func.now())

# CREATE - Cria uma nova carreira
def criar_carreira(session, nome, descricao):
	nova_carreira = Carreira(nome=nome, descricao=descricao)
	session.add(nova_carreira)
	session.commit()
	session.refresh(nova_carreira)
	return nova_carreira.id

# READ - Lista todas as carreiras
def listar_carreiras(session):
	return session.query(Carreira).all()

# READ - Busca uma carreira pelo id
def buscar_carreira_por_id(session, id):
	return session.query(Carreira).filter(Carreira.id == id).first()

# UPDATE - Atualiza os dados de uma carreira existente
def atualizar_carreira(session, id, nome=None, descricao=None, atualizado_em=None):
	carreira = session.query(Carreira).filter(Carreira.id == id).first()
	if carreira:
		if nome:
			carreira.nome = nome
		if descricao:
			carreira.descricao = descricao
		if atualizado_em:
			carreira.atualizado_em = atualizado_em
		session.commit()
	return carreira

# DELETE - Remove uma carreira pelo id
def deletar_carreira(session, id):
	carreira = session.query(Carreira).filter(Carreira.id == id).first()
	if carreira:
		session.delete(carreira)
		session.commit()
	return carreira