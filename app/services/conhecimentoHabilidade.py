from app.models import ConhecimentoHabilidade # modelo de tabela definido no arquivo models.py
from app.dependencies import setup_database # conexão do banco de dados
from app.schemas import ConhecimentoHabilidadeBase, ConhecimentoHabilidadeOut # schema de entrada e saída

engine, SessionLocal, Base = setup_database()

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# CREATE / POST - Cria uma nova relação entre habilidade e conhecimento
def criar_conhecimento_habilidade(session, conhecimento_habilidade_data: ConhecimentoHabilidadeBase) -> ConhecimentoHabilidadeOut:
    nova = ConhecimentoHabilidade(**conhecimento_habilidade_data.model_dump())
    session.add(nova)
    session.commit()
    session.refresh(nova)
    return ConhecimentoHabilidadeOut.model_validate(nova)

# READ / GET - Lista todas as habilidades do conhecimento
def listar_conhecimento_habilidades(session, conhecimento_id: int) -> list[ConhecimentoHabilidadeOut]:
    habilidades = session.query(ConhecimentoHabilidade).filter_by(conhecimento_id=conhecimento_id).all()
    return [ConhecimentoHabilidadeOut.model_validate(h) for h in habilidades]

# DELETE / DELETE - Remove uma habilidade do conhecimento
def remover_conhecimento_habilidade(session, conhecimento_id: int, habilidade_id: int) -> ConhecimentoHabilidadeOut | None:
    relacao = session.query(ConhecimentoHabilidade).filter_by(conhecimento_id=conhecimento_id, habilidade_id=habilidade_id).first()
    if relacao:
        session.delete(relacao)
        session.commit()
        return ConhecimentoHabilidadeOut.model_validate(relacao)
    return None
