from app.models.carreiraModels import Carreira 
from app.schemas.carreiraSchemas import CarreiraBase, CarreiraOut 


def criar_carreira(session, carreira_data: CarreiraBase) -> CarreiraOut:
    """Cria uma nova carreira no banco de dados a partir dos dados do schema, salva e retorna como CarreiraOut"""
    nova_carreira = Carreira(**carreira_data.model_dump())
    session.add(nova_carreira)
    session.commit()
    session.refresh(nova_carreira)
    return CarreiraOut.model_validate(nova_carreira)


def listar_carreiras(session) -> list[CarreiraOut]:
    """Busca todas as carreiras no banco de dados e retorna uma lista convertida para CarreiraOut"""
    carreiras = session.query(Carreira).all()
    return [CarreiraOut.model_validate(carreira) for carreira in carreiras]


def buscar_carreira_por_id(session, id: int) -> CarreiraOut | None:
    """Busca uma carreira específica pelo ID no banco de dados e retorna como CarreiraOut ou None se não encontrada"""
    carreira = session.query(Carreira).filter(Carreira.id == id).first()
    return CarreiraOut.model_validate(carreira) if carreira else None


def atualizar_carreira(session, id: int, carreira_data: CarreiraBase) -> CarreiraOut | None:
    """Busca uma carreira pelo ID, atualiza apenas os campos informados no schema, salva no banco e retorna como CarreiraOut"""
    carreira = session.query(Carreira).filter(Carreira.id == id).first()
    if carreira:
        for key, value in carreira_data.model_dump(exclude_unset=True).items():
            setattr(carreira, key, value)
        session.commit()
        session.refresh(carreira)
        return CarreiraOut.model_validate(carreira)
    return None


def deletar_carreira(session, id: int) -> CarreiraOut | None:
    """Busca uma carreira pelo ID, remove do banco de dados e retorna os dados da carreira removida como CarreiraOut"""
    carreira = session.query(Carreira).filter(Carreira.id == id).first()
    if carreira:
        session.delete(carreira)
        session.commit()
        return CarreiraOut.model_validate(carreira)
    return None
