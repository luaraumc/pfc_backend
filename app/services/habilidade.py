from app.models.habilidadeModels import Habilidade 
from app.models.categoriaModels import Categoria
from app.schemas.habilidadeSchemas import HabilidadeOut, HabilidadeAtualizar
from sqlalchemy.orm import joinedload


def listar_habilidades(session) -> list[HabilidadeOut]:
    """Busca todas as habilidades no banco de dados e retorna uma lista convertida para HabilidadeOut"""
    habilidades = session.query(Habilidade).all()
    return [HabilidadeOut.model_validate(habilidade) for habilidade in habilidades]


def buscar_habilidade_por_id(session, id: int) -> HabilidadeOut | None:
    """Busca uma habilidade específica pelo ID no banco de dados e retorna como HabilidadeOut ou None se não encontrada"""
    habilidade = session.query(Habilidade).filter(Habilidade.id == id).first()
    return HabilidadeOut.model_validate(habilidade) if habilidade else None


def atualizar_habilidade(session, id: int, habilidade_data: HabilidadeAtualizar) -> HabilidadeOut | None:
    """Busca uma habilidade pelo ID, atualiza nome e/ou categoria se informados, salva no banco e retorna como HabilidadeOut"""
    habilidade = session.query(Habilidade).filter(Habilidade.id == id).first()
    if habilidade:
        data = habilidade_data.model_dump(exclude_unset=True)
        nome = data.get('nome')
        if isinstance(nome, str) and nome.strip():
            habilidade.nome = nome.strip()
        cat_id = data.get('categoria_id')
        if cat_id is not None:
            categoria = session.query(Categoria).filter(Categoria.id == cat_id).first()
            if not categoria:
                return None
            habilidade.categoria_id = categoria.id
        session.commit()
        session.refresh(habilidade)
        return HabilidadeOut.model_validate(habilidade)
    return None


def deletar_habilidade(session, id: int) -> HabilidadeOut | None:
    """Busca uma habilidade pelo ID com relação de categoria carregada, remove do banco e retorna os dados removidos"""
    habilidade = (
        session.query(Habilidade)
        .options(joinedload(Habilidade.categoria_rel))
        .filter(Habilidade.id == id)
        .first()
    )
    if habilidade:
        dto = HabilidadeOut.model_validate(habilidade)
        session.delete(habilidade)
        session.commit()
        return dto
    return None
