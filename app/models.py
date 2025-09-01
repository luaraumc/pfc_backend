from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, UniqueConstraint # tipos de dados e restrições
from sqlalchemy.sql import func # permite usar funções SQL, como NOW() para timestamps automáticos
from sqlalchemy.orm import relationship # cria relacionamentos entre tabelas
from app.dependencies import setup_database # configuração da conexão com o banco de dados



engine, SessionLocal, Base = setup_database()

# ===================== TABELAS PRINCIPAIS =====================

# Modelo da tabela curso
class Curso(Base):
	__tablename__ = 'curso'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), nullable=False)
	descricao = Column(Text, nullable=False)
	atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)

# Modelo tabela "carreira"
class Carreira(Base):
	__tablename__ = 'carreira'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), nullable=False)
	descricao = Column(Text)
	atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)

# Modelo da tabela "usuario"
class Usuario(Base):
	__tablename__ = 'usuario'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(100), nullable=False)
	email = Column(String(150), unique=True, nullable=False)
	senha = Column(Text, nullable=False)
	carreira_id = Column(Integer, ForeignKey('carreira.id', ondelete='SET NULL'), nullable=False)
	curso_id = Column(Integer, ForeignKey('curso.id', ondelete='SET NULL'), nullable=False)
	criado_em = Column(DateTime, server_default=func.now(), nullable=False)
	atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)
	carreira = relationship('Carreira', backref='usuarios')
	curso = relationship('Curso', backref='usuarios')

# Modelo da tabela "habilidade"
class Habilidade(Base):
	__tablename__ = 'habilidade'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), unique=True, nullable=False)
	atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)

# Modelo da tabela "conhecimento"
class Conhecimento(Base):
	__tablename__ = 'conhecimento'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), unique=True, nullable=False)
	atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)

# Modelo da tabela "compatibilidade"
class Compatibilidade(Base):
	__tablename__ = 'compatibilidade'
	id = Column(Integer, primary_key=True, index=True)
	usuario_id = Column(Integer, ForeignKey('usuario.id', ondelete='SET NULL'), nullable=False)
	carreira_id = Column(Integer, ForeignKey('carreira.id', ondelete='SET NULL'), nullable=False)
	curso_id = Column(Integer, ForeignKey('curso.id', ondelete='SET NULL'), nullable=False)
	compatibilidade = Column(Numeric(5,2), nullable=False)
	atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)
	usuario = relationship('Usuario', backref='compatibilidades')
	carreira = relationship('Carreira', backref='compatibilidades')
	curso = relationship('Curso', backref='compatibilidades')
	
# backref: cria um relacionamento bidirecional entre os modelos

# ===================== TABELAS RELACIONAIS =====================

class CursoConhecimento(Base):
    __tablename__ = 'curso_conhecimento'
    id = Column(Integer, primary_key=True, index=True)
    curso_id = Column(Integer, ForeignKey('curso.id', ondelete='CASCADE'), nullable=False)
    conhecimento_id = Column(Integer, ForeignKey('conhecimento.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (
        UniqueConstraint('curso_id', 'conhecimento_id', name='uq_curso_conhecimento'),
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

# ondelete='CASCADE': garante que ao excluir o registro principal os relacionados também sejam excluídos
# UniqueConstraint: garante que não haja duplicidade