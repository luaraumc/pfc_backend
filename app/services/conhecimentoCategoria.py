from app.models.conhecimentoCategoriaModels import ConhecimentoCategoria  # modelo de tabela 
from app.schemas.conhecimentoCategoriaSchemas import ConhecimentoCategoriaBase, ConhecimentoCategoriaOut, ConhecimentoCategoriaAtualizar  # schemas

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

# UPDATE / PUT - Atualiza categoria_id e/ou peso da relação (parcial)
def atualizar_conhecimento_categoria(session, relacao_id: int, data: ConhecimentoCategoriaAtualizar) -> ConhecimentoCategoriaOut | None:
    relacao = session.query(ConhecimentoCategoria).filter_by(id=relacao_id).first()
    if not relacao:
        return None
    payload = data.model_dump(exclude_unset=True)
    # Se categoria_id foi informado, atualiza
    if 'categoria_id' in payload and payload['categoria_id'] is not None:
        relacao.categoria_id = payload['categoria_id']
    # Se peso foi informado, atualiza (pode ser None para limpar)
    if 'peso' in payload:
        relacao.peso = payload['peso']
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(relacao)
    return ConhecimentoCategoriaOut.model_validate(relacao)

