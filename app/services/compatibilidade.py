from pfc_backend.app.models import Compatibilidade # modelo de tabela definido no arquivo models.py
from pfc_backend.app.models import setup_database # conexão do banco de dados

engine, SessionLocal, Base = setup_database()

# ======================= CRUD =======================

# CREATE - Cria uma nova compatibilidade
def criar_compatibilidade(session, usuario_id, carreira_id, curso_id, compatibilidade):
    nova_compatibilidade = Compatibilidade(usuario_id=usuario_id, carreira_id=carreira_id, curso_id=curso_id, compatibilidade=compatibilidade)
    session.add(nova_compatibilidade)
    session.commit()
    session.refresh(nova_compatibilidade)
    return nova_compatibilidade.id

# READ - Lista todas as compatibilidades
def listar_compatibilidades(session):
    return session.query(Compatibilidade).all()

# READ - Busca uma compatibilidade pelo id
def buscar_compatibilidade_por_id(session, id):
    return session.query(Compatibilidade).filter(Compatibilidade.id == id).first()

# UPDATE - Atualiza os dados de uma compatibilidade existente
def atualizar_competibilidade(session, id, usuario_id=None, carreira_id=None, curso_id=None, compatibilidade=None):
    compatibilidade = session.query(Compatibilidade).filter(Compatibilidade.id == id).first()
    if compatibilidade:
        if usuario_id:
            compatibilidade.usuario_id = usuario_id
        if carreira_id:
            compatibilidade.carreira_id = carreira_id
        if curso_id:
            compatibilidade.curso_id = curso_id
        if compatibilidade:
            compatibilidade.compatibilidade = compatibilidade
        session.commit()
    return compatibilidade

# DELETE - Remove uma compatibilidade pelo id
def deletar_compatibilidade(session, id):
    compatibilidade = session.query(Compatibilidade).filter(Compatibilidade.id == id).first()
    if compatibilidade:
        session.delete(compatibilidade)
        session.commit()
    return compatibilidade
