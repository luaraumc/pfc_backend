from app.models.conhecimentoCategoriaModels import ConhecimentoCategoria
from app.schemas.conhecimentoCategoriaSchemas import ConhecimentoCategoriaBase, ConhecimentoCategoriaOut, ConhecimentoCategoriaAtualizar


def criar_conhecimento_categoria(session, conhecimento_categoria_data: ConhecimentoCategoriaBase) -> ConhecimentoCategoriaOut:
    """Cria uma nova relação entre categoria e conhecimento no banco de dados e retorna como ConhecimentoCategoriaOut"""
    nova = ConhecimentoCategoria(**conhecimento_categoria_data.model_dump())
    session.add(nova)
    session.commit()
    session.refresh(nova)
    return ConhecimentoCategoriaOut.model_validate(nova)


def listar_conhecimento_categorias(session, conhecimento_id: int) -> list[ConhecimentoCategoriaOut]:
    """Lista todas as categorias associadas a um conhecimento específico e retorna como lista de ConhecimentoCategoriaOut"""
    registros = session.query(ConhecimentoCategoria).filter_by(conhecimento_id=conhecimento_id).all()
    return [ConhecimentoCategoriaOut.model_validate(h) for h in registros]


def remover_conhecimento_categoria(session, conhecimento_id: int, categoria_id: int) -> ConhecimentoCategoriaOut | None:
    """Remove a associação entre um conhecimento e uma categoria específica e retorna os dados removidos ou None se não encontrada"""
    relacao = session.query(ConhecimentoCategoria).filter_by(conhecimento_id=conhecimento_id, categoria_id=categoria_id).first()
    if relacao:
        session.delete(relacao)
        session.commit()
        return ConhecimentoCategoriaOut.model_validate(relacao)
    return None


def atualizar_conhecimento_categoria(session, relacao_id: int, data: ConhecimentoCategoriaAtualizar) -> ConhecimentoCategoriaOut | None:
    """Atualiza parcialmente uma relação conhecimento-categoria existente atualizando apenas os campos informados"""
    relacao = session.query(ConhecimentoCategoria).filter_by(id=relacao_id).first()
    if not relacao:
        return None
    payload = data.model_dump(exclude_unset=True)
    if 'categoria_id' in payload and payload['categoria_id'] is not None:
        relacao.categoria_id = payload['categoria_id']
    if 'peso' in payload:
        relacao.peso = payload['peso']
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
    session.refresh(relacao)
    return ConhecimentoCategoriaOut.model_validate(relacao)
