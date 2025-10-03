from app.models import VagaHabilidade, Habilidade # modelo de tabela definido no arquivo models.py
from app.schemas import VagaHabilidadeBase, VagaHabilidadeOut # schema de entrada e saída
from typing import List # tipos para listas

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# CREATE / POST - Cria uma nova relação vaga-habilidade
def criar_relacao_vaga_habilidade(session, vaga_id: int, habilidade_id: int) -> VagaHabilidade:
    existente = session.query(VagaHabilidade).filter_by(vaga_id=vaga_id, habilidade_id=habilidade_id).first()
    if existente:
        return existente
    relacao = VagaHabilidade(vaga_id=vaga_id, habilidade_id=habilidade_id)
    session.add(relacao)
    session.commit()
    session.refresh(relacao)
    return relacao

# READ / GET - Lista todas as habilidades associadas a uma vaga
def listar_habilidades_por_vaga(session, vaga_id: int) -> List[Habilidade]:
    return (
        session.query(Habilidade)
        .join(VagaHabilidade, VagaHabilidade.habilidade_id == Habilidade.id)
        .filter(VagaHabilidade.vaga_id == vaga_id)
        .order_by(Habilidade.nome.asc())
        .all()
    )

# DELETE / DELETE - Remove a relação vaga-habilidade
def remover_relacao_vaga_habilidade(session, vaga_id: int, habilidade_id: int) -> bool:
    relacao = (
        session.query(VagaHabilidade)
        .filter_by(vaga_id=vaga_id, habilidade_id=habilidade_id)
        .first()
    )
    if not relacao:
        return False
    session.delete(relacao)
    session.commit()
    return True