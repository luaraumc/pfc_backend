from app.models.carreiraHabilidadeModels import CarreiraHabilidade # modelo de tabela
from app.schemas.carreiraHabilidadeSchemas import CarreiraHabilidadeBase, CarreiraHabilidadeOut # schema de entrada e saída

# ======================= CRUD =======================

# CREATE / POST - Cria uma nova relação entre habilidade e carreira
def criar_carreira_habilidade(session, carreira_habilidade_data: CarreiraHabilidadeBase) -> CarreiraHabilidadeOut:
    """Cria uma nova associação entre carreira e habilidade no banco de dados e retorna como CarreiraHabilidadeOut"""
    nova = CarreiraHabilidade(**carreira_habilidade_data.model_dump())
    session.add(nova)
    session.commit()
    session.refresh(nova)
    return CarreiraHabilidadeOut.model_validate(nova)

# READ / GET - Lista todas as habilidades da carreira
def listar_carreira_habilidades(session, carreira_id: int) -> list[CarreiraHabilidadeOut]:
    """Lista todas as habilidades associadas a uma carreira específica e retorna como lista de CarreiraHabilidadeOut"""
    habilidades = session.query(CarreiraHabilidade).filter_by(carreira_id=carreira_id).all()
    return [CarreiraHabilidadeOut.model_validate(h) for h in habilidades]

# DELETE / DELETE - Remove uma habilidade da carreira
def remover_carreira_habilidade(session, carreira_id: int, habilidade_id: int) -> CarreiraHabilidadeOut | None:
    """Remove a associação entre uma carreira e uma habilidade específica e retorna os dados removidos ou None se não encontrada"""
    relacao = session.query(CarreiraHabilidade).filter_by(carreira_id=carreira_id, habilidade_id=habilidade_id).first()
    if relacao:
        session.delete(relacao)
        session.commit()
        return CarreiraHabilidadeOut.model_validate(relacao)
    return None
