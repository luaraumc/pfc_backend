from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Modelo da tabela cursos
class Curso(Base):
	__tablename__ = 'cursos'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), nullable=False)
	descricao = Column(Text, nullable=False)
	criado_em = Column(DateTime, server_default=func.now())
	atualizado_em = Column(DateTime, server_default=func.now())

# Modelo tabela "carreiras"
class Carreira(Base):
	__tablename__ = 'carreiras'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), nullable=False)
	descricao = Column(Text, nullable=False)
	criado_em = Column(DateTime, server_default=func.now())
	atualizado_em = Column(DateTime, server_default=func.now())

# Modelo da tabela "usuarios"
class Usuario(Base):
	__tablename__ = 'usuarios'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(100), nullable=False)
	email = Column(String(150), nullable=False)
	senha = Column(Text, nullable=False)
	curso_id = Column(Integer, ForeignKey('cursos.id', ondelete='SET NULL'), nullable=True)
	criado_em = Column(DateTime, server_default=func.now())
	atualizado_em = Column(DateTime, server_default=func.now())
	curso = relationship('Curso', backref='usuarios')

