from models import Habilidade # modelo de tabela definido no arquivo models.py
from models import setup_database # conexão do banco de dados

engine, SessionLocal, Base = setup_database()

# ======================= CRUD =======================

# CREATE - Cria uma nova habilidade
def criar_habilidade(session, nome):
    nova_habilidade = Habilidade(nome=nome)
    session.add(nova_habilidade)
    session.commit()
    session.refresh(nova_habilidade)
    return nova_habilidade.id

# READ - Lista todas as habilidades
def listar_habilidade(session):
    return session.query(Habilidade).all()

# READ - Busca uma habilidade pelo id
def buscar_habilidade_por_id(session, id):
    return session.query(Habilidade).filter(Habilidade.id == id).first()

# UPDATE - Atualiza os dados de uma habilidade existente
def atualizar_habilidade(session, id, nome=None):
    habilidade = session.query(Habilidade).filter(Habilidade.id == id).first()
    if habilidade:
        if nome:
            habilidade.nome = nome
        session.commit()
    return habilidade

# DELETE - Remove uma habilidade pelo id
def deletar_habilidade(session, id):
    habilidade = session.query(Habilidade).filter(Habilidade.id == id).first()
    if habilidade:
        session.delete(habilidade)
        session.commit()
    return habilidade

