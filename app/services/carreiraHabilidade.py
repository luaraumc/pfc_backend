from app.models import CarreiraHabilidade # modelo de tabela definido no arquivo models.py
from app.schemas import CarreiraHabilidadeBase, CarreiraHabilidadeOut # schema de entrada e saída

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# CREATE / POST - Cria ou incrementa uma relação entre habilidade e carreira
def criar_carreira_habilidade(session, carreira_habilidade_data: CarreiraHabilidadeBase) -> CarreiraHabilidadeOut:
    existente = session.query(CarreiraHabilidade).filter_by(
        carreira_id=carreira_habilidade_data.carreira_id,
        habilidade_id=carreira_habilidade_data.habilidade_id
    ).first()
    if existente:
        # incrementa frequência automaticamente
        existente.frequencia = (existente.frequencia or 0) + 1
        session.commit()
        session.refresh(existente)
        return CarreiraHabilidadeOut.model_validate(existente)
    nova = CarreiraHabilidade(
        carreira_id=carreira_habilidade_data.carreira_id,
        habilidade_id=carreira_habilidade_data.habilidade_id,
        frequencia=1
    )
    session.add(nova)
    session.commit()
    session.refresh(nova)
    return CarreiraHabilidadeOut.model_validate(nova)

# READ / GET - Lista todas as habilidades da carreira
def listar_carreira_habilidades(session, carreira_id: int) -> list[CarreiraHabilidadeOut]:
    habilidades = session.query(CarreiraHabilidade).filter_by(carreira_id=carreira_id).all()
    return [CarreiraHabilidadeOut.model_validate(h) for h in habilidades]

# DELETE / DELETE - Remove uma habilidade da carreira
def remover_carreira_habilidade(session, carreira_id: int, habilidade_id: int) -> CarreiraHabilidadeOut | None:
    relacao = session.query(CarreiraHabilidade).filter_by(carreira_id=carreira_id, habilidade_id=habilidade_id).first()
    if relacao:
        session.delete(relacao)
        session.commit()
        return CarreiraHabilidadeOut.model_validate(relacao)
    return None
