from sqlalchemy import create_engine # cria a conexão com o banco de dados
from sqlalchemy.ext.declarative import declarative_base # declarative_base: base para a criação dos modelos ORM
from sqlalchemy.orm import sessionmaker # sessionmaker: cria sessões para manipular o banco
from sqlalchemy.sql import func # func permite usar funções SQL nativas, como NOW() para datetime
import os # acessa variáveis de ambiente do sistema
from models import Carreira # modelos de tabelas definidos no arquivo models.py
from dotenv import load_dotenv # carrega variáveis de ambiente

# Configuração da conexão
load_dotenv()
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URL)  # Cria o objeto de conexão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # Gera sessões para executar operações
Base = declarative_base()  # Base para definição dos modelos ORM (tabelas)

# ======================= CRUD =======================

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