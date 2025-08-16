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

# Modelo da tabela cursos
class Curso(Base):
	__tablename__ = 'cursos'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), nullable=False)
	descricao = Column(Text, nullable=False)
	criado_em = Column(DateTime, server_default=func.now())
	atualizado_em = Column(DateTime, server_default=func.now())

# CREATE - Cria um novo curso
def criar_curso(session, nome, descricao):
	novo_curso = Curso(nome=nome, descricao=descricao)
	session.add(novo_curso)
	session.commit()
	session.refresh(novo_curso)
	return novo_curso.id

# READ - Lista todos os cursos
def listar_cursos(session):
	return session.query(Curso).all()

# READ - Busca um curso pelo id
def buscar_curso_por_id(session, id):
	return session.query(Curso).filter(Curso.id == id).first()

# UPDATE - Atualiza os dados de um curso existente
def atualizar_curso(session, id, nome=None, descricao=None, atualizado_em=None):
	curso = session.query(Curso).filter(Curso.id == id).first()
	if curso:
		if nome:
			curso.nome = nome
		if descricao:
			curso.descricao = descricao
		if atualizado_em:
			curso.atualizado_em = atualizado_em
		session.commit()
	return curso

# DELETE - Remove um curso pelo id
def deletar_curso(session, id):
	curso = session.query(Curso).filter(Curso.id == id).first()
	if curso:
		session.delete(curso)
		session.commit()
	return curso
