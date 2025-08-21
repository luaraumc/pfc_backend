from sqlalchemy import create_engine # cria a conexão com o banco de dados
from sqlalchemy.ext.declarative import declarative_base # declarative_base: base para a criação dos modelos ORM
from sqlalchemy.orm import sessionmaker, relationship # sessionmaker: cria sessões para manipular o banco / relationship: gerencia conexões entre diferentes tabelas
from sqlalchemy.sql import func # func permite usar funções SQL nativas, como NOW() para datetime
import os # acessa variáveis de ambiente do sistema
from models import Usuario, Curso, Carreira # modelos de tabelas definidos no arquivo models.py
from dotenv import load_dotenv # carrega variáveis de ambiente

# Configuração da conexão
load_dotenv()
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)  # Cria o objeto de conexão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # Gera sessões para executar operações
Base = declarative_base()  # Base para definição dos modelos ORM (tabelas)

# ======================= CRUD =======================

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