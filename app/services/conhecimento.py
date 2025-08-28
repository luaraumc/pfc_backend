from pfc_backend.app.models import Conhecimento # modelo de tabela definido no arquivo models.py
from pfc_backend.app.models import setup_database # conexão do banco de dados

engine, SessionLocal, Base = setup_database()

# ======================= CRUD =======================

# CREATE - Cria um novo conhecimento
def criar_conhecimento(session, nome):
    novo_conhecimento = Conhecimento(nome=nome)
    session.add(novo_conhecimento)
    session.commit()
    session.refresh(novo_conhecimento)
    return novo_conhecimento.id

# READ - Lista todos os conhecimentos
def listar_conhecimentos(session):
    return session.query(Conhecimento).all()

# READ - Busca um conhecimento pelo id
def buscar_conhecimento_por_id(session, id):
    return session.query(Conhecimento).filter(Conhecimento.id == id).first()

# UPDATE - Atualiza os dados de um conhecimento existente
def atualizar_conhecimento(session, id, nome=None):
    conhecimento = session.query(Conhecimento).filter(Conhecimento.id == id).first()
    if conhecimento:
        if nome:
            conhecimento.nome = nome
        session.commit()
    return conhecimento

# DELETE - Remove um conhecimento pelo id
def deletar_conhecimento(session, id):
    conhecimento = session.query(Conhecimento).filter(Conhecimento.id == id).first()
    if conhecimento:
        session.delete(conhecimento)
        session.commit()
    return conhecimento

# DELETE - Remove um conhecimento pelo id
def deletar_conhecimento(session, id):
    conhecimento = session.query(Conhecimento).filter(Conhecimento.id == id).first()
    if conhecimento:
        session.delete(conhecimento)
        session.commit()
    return conhecimento