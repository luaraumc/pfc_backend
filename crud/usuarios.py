from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
# create_engine: cria a conexão com o banco de dados
# Column, Integer, String, Text, DateTime, ForeignKey: definem os tipos e colunas das tabelas

from sqlalchemy.ext.declarative import declarative_base
# declarative_base: base para a criação dos modelos ORM

from sqlalchemy.orm import sessionmaker, relationship
# sessionmaker: cria sessões para manipular o banco
# relationship: gerencia conexões entre diferentes tabelas

from sqlalchemy.sql import func
# func permite usar funções SQL nativas, como NOW() para datetime

import os
# acessa variáveis de ambiente do sistema

# Configuração da conexão
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL)  # Cria o objeto de conexão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # Gera sessões para executar operações
Base = declarative_base()  # Base para definição dos modelos ORM (tabelas)

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

# Modelo da tabela cursos (para garantir o funcionamento da relação)
class Curso(Base):
	__tablename__ = 'cursos'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), nullable=False)
	descricao = Column(Text, nullable=False)
	criado_em = Column(DateTime, server_default=func.now())
	atualizado_em = Column(DateTime, server_default=func.now())

# CREATE - Cria um novo usuário
def criar_usuario(session, nome, email, senha, curso_id):
    novo_usuario = Usuario(nome=nome, email=email, senha=senha, curso_id=curso_id)
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)
    return novo_usuario.id

# READ - Lista todos os usuários
def listar_usuarios(session):
    return session.query(Usuario).all()

# READ - Busca um usuário pelo id
def buscar_usuario_por_id(session, id):
    return session.query(Usuario).filter(Usuario.id == id).first()

# UPDATE - Atualiza os dados de um usuário existente
def atualizar_usuario(session, id, nome=None, email=None, senha=None, atualizado_em=None):
    usuario = session.query(Usuario).filter(Usuario.id == id).first()
    if usuario:
        if nome:
            usuario.nome = nome
        if email:
            usuario.email = email
        if senha:
            usuario.senha = senha
        if atualizado_em:
            usuario.atualizado_em = atualizado_em
        session.commit()
    return usuario

# DELETE - Remove um usuário pelo id
def deletar_usuario(session, id):
    usuario = session.query(Usuario).filter(Usuario.id == id).first()
    if usuario:
        session.delete(usuario)
        session.commit()
    return usuario