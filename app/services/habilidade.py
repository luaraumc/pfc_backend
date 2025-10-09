from app.models import Habilidade # modelo de tabela definido no arquivo models.py
from app.schemas import HabilidadeBase, HabilidadeOut # schema de entrada e saída

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# READ - Lista todas as habilidades
def listar_habilidades(session) -> list[HabilidadeOut]:
    habilidades = session.query(Habilidade).all()  # Busca todas as habilidades no banco
    return [HabilidadeOut.model_validate(habilidade) for habilidade in habilidades] # Converte cada habilidade para o schema de saída

# READ - Busca uma habilidade pelo id
def buscar_habilidade_por_id(session, id: int) -> HabilidadeOut | None:
    habilidade = session.query(Habilidade).filter(Habilidade.id == id).first()  # Busca a habilidade pelo id
    return HabilidadeOut.model_validate(habilidade) if habilidade else None # Se encontrada converte para schema de saída, senão retorna None

# DELETE - Remove uma habilidade pelo id
def deletar_habilidade(session, id: int) -> HabilidadeOut | None:
    habilidade = session.query(Habilidade).filter(Habilidade.id == id).first()  # Busca a habilidade pelo id
    if habilidade:
        session.delete(habilidade)  # Remove do banco
        session.commit()
        return HabilidadeOut.model_validate(habilidade) # Retorna a habilidade removida como schema de saída
    return None
