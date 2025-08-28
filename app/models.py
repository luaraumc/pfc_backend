from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy import create_engine # cria a conexão com o banco de dados
from sqlalchemy.sql import func # permite usar funções SQL, como NOW() para timestamps automáticos
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.orm import sessionmaker # cria sessões para manipular o banco
from dotenv import load_dotenv
import os

# Configuração da conexão
load_dotenv()
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)  # Cria o objeto de conexão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # Gera sessões para executar operações
Base = declarative_base() # classe utilizada para criar os modelos ORM que representam as tabelas do banco de dados

# ===================== TABELAS PRINCIPAIS =====================

# Modelo da tabela curso
class Curso(Base):
	__tablename__ = 'curso'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), nullable=False)
	descricao = Column(Text, nullable=False)
	atualizado_em = Column(DateTime, server_default=func.now())

# Modelo tabela "carreira"
class Carreira(Base):
	__tablename__ = 'carreira'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), nullable=False)
	descricao = Column(Text)
	atualizado_em = Column(DateTime, server_default=func.now())


# Modelo da tabela "usuario"
class Usuario(Base):
	__tablename__ = 'usuario'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(100), nullable=False)
	email = Column(String(150), unique=True, nullable=False)
	senha = Column(Text, nullable=False)
	carreira_id = Column(Integer, ForeignKey('carreira.id', ondelete='SET NULL'), nullable=True)
	curso_id = Column(Integer, ForeignKey('curso.id', ondelete='SET NULL'), nullable=True)
	criado_em = Column(DateTime, server_default=func.now())
	atualizado_em = Column(DateTime, server_default=func.now())
	carreira = relationship('Carreira', backref='usuarios')
	curso = relationship('Curso', backref='usuarios')
	# relationship: permite acessar a carreira e curso relacionados a um usuario
	# backref: cria uma lista de usuarios acessível a partir de cada carreira ou curso


# Modelo da tabela "habilidade"
class Habilidade(Base):
	__tablename__ = 'habilidade'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), unique=True, nullable=False)
	atualizado_em = Column(DateTime, server_default=func.now())


# Modelo da tabela "conhecimento"
class Conhecimento(Base):
	__tablename__ = 'conhecimento'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), unique=True, nullable=False)
	atualizado_em = Column(DateTime, server_default=func.now())


# Modelo da tabela "compatibilidade"
class Compatibilidade(Base):
	__tablename__ = 'compatibilidade'
	id = Column(Integer, primary_key=True, index=True)
	usuario_id = Column(Integer, ForeignKey('usuario.id', ondelete='SET NULL'), nullable=True)
	carreira_id = Column(Integer, ForeignKey('carreira.id', ondelete='SET NULL'), nullable=True)
	curso_id = Column(Integer, ForeignKey('curso.id', ondelete='SET NULL'), nullable=True)
	compatibilidade = Column(Numeric(5,2))
	atualizado_em = Column(DateTime, server_default=func.now())
	usuario = relationship('Usuario', backref='compatibilidades')
	carreira = relationship('Carreira', backref='compatibilidades')
	curso = relationship('Curso', backref='compatibilidades')
	# relationship: permite acessar usuário, carreira e curso relacionados a uma compatibilidade
	# backref: cria uma lista de compatibilidades acessível a partir de cada usuário, carreira ou curso


# ===================== TABELAS RELACIONAIS =====================

class CursoConhecimento(Base):
    __tablename__ = 'curso_conhecimento'
    id = Column(Integer, primary_key=True, index=True)
    curso_id = Column(Integer, ForeignKey('curso.id', ondelete='CASCADE'), nullable=False)
    conhecimento_id = Column(Integer, ForeignKey('conhecimento.id', ondelete='CASCADE'), nullable=False) # ondelete='CASCADE': garante que ao excluir o registro principal os relacionados também sejam excluídos
    __table_args__ = (
        UniqueConstraint('curso_id', 'conhecimento_id', name='uq_curso_conhecimento'), # UniqueConstraint: garante que não haja duplicidade
    )


class CarreiraHabilidade(Base):
    __tablename__ = 'carreira_habilidade'
    id = Column(Integer, primary_key=True, index=True)
    carreira_id = Column(Integer, ForeignKey('carreira.id', ondelete='CASCADE'), nullable=False)
    habilidade_id = Column(Integer, ForeignKey('habilidade.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (
        UniqueConstraint('carreira_id', 'habilidade_id', name='uq_carreira_habilidade'),
    )

class UsuarioHabilidade(Base):
    __tablename__ = 'usuario_habilidade'
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    habilidade_id = Column(Integer, ForeignKey('habilidade.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (
        UniqueConstraint('usuario_id', 'habilidade_id', name='uq_usuario_habilidade'),
    )

class ConhecimentoHabilidade(Base):
    __tablename__ = 'conhecimento_habilidade'
    id = Column(Integer, primary_key=True, index=True)
    conhecimento_id = Column(Integer, ForeignKey('conhecimento.id', ondelete='CASCADE'), nullable=False)
    habilidade_id = Column(Integer, ForeignKey('habilidade.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (
        UniqueConstraint('conhecimento_id', 'habilidade_id', name='uq_conhecimento_habilidade'),
    )
