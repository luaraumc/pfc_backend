from app.models import ConhecimentoCategoria  # modelo de tabela definido no arquivo models.py
from app.schemas import ConhecimentoCategoriaBase, ConhecimentoCategoriaOut  # schema de entrada e saída

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# CREATE / POST - Cria uma nova relação entre categoria e conhecimento
def criar_conhecimento_categoria(session, conhecimento_categoria_data: ConhecimentoCategoriaBase) -> ConhecimentoCategoriaOut:
    nova = ConhecimentoCategoria(**conhecimento_categoria_data.model_dump())
    session.add(nova)
    session.commit()
    session.refresh(nova)
    return ConhecimentoCategoriaOut.model_validate(nova)

# READ / GET - Lista todas as categorias do conhecimento
def listar_conhecimento_categorias(session, conhecimento_id: int) -> list[ConhecimentoCategoriaOut]:
    registros = session.query(ConhecimentoCategoria).filter_by(conhecimento_id=conhecimento_id).all()
    return [ConhecimentoCategoriaOut.model_validate(h) for h in registros]

# DELETE / DELETE - Remove uma categoria do conhecimento
def remover_conhecimento_categoria(session, conhecimento_id: int, categoria_id: int) -> ConhecimentoCategoriaOut | None:
    relacao = session.query(ConhecimentoCategoria).filter_by(conhecimento_id=conhecimento_id, categoria_id=categoria_id).first()
    if relacao:
        session.delete(relacao)
        session.commit()
        return ConhecimentoCategoriaOut.model_validate(relacao)
    return None

