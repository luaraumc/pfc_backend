from app.models.carreira import Carreira # modelo de tabela 
from app.schemas import CarreiraBase, CarreiraOut # schema de entrada e saída

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# CREATE / POST - Cria uma nova carreira
def criar_carreira(session, carreira_data: CarreiraBase) -> CarreiraOut:
    nova_carreira = Carreira(**carreira_data.model_dump()) # Cria um objeto Carreira a partir dos dados do schema (Pydantic)
    session.add(nova_carreira)  # Adiciona no banco
    session.commit() # Salva no banco
    session.refresh(nova_carreira) # Atualiza o objeto com dados do banco
    return CarreiraOut.model_validate(nova_carreira) # Converte o modelo SQLAlchemy para o schema de saída (CarreiraOut)

# READ / GET - Lista todas as carreiras
def listar_carreiras(session) -> list[CarreiraOut]:
    carreiras = session.query(Carreira).all()  # Busca todas as carreiras no banco
    return [CarreiraOut.model_validate(carreira) for carreira in carreiras] # Converte cada carreira para o schema de saída

# READ / GET - Busca uma carreira pelo id
def buscar_carreira_por_id(session, id: int) -> CarreiraOut | None:
    carreira = session.query(Carreira).filter(Carreira.id == id).first()  # Busca a carreira pelo id
    return CarreiraOut.model_validate(carreira) if carreira else None # Se encontrada converte para schema de saída, senão retorna None

# UPDATE / PUT - Atualiza os dados de uma carreira existente usando schema
def atualizar_carreira(session, id: int, carreira_data: CarreiraBase) -> CarreiraOut | None:
    carreira = session.query(Carreira).filter(Carreira.id == id).first()  # Busca a carreira pelo id
    if carreira:
        # Atualiza os campos da carreira com os dados recebidos
        for key, value in carreira_data.model_dump(exclude_unset=True).items():
            setattr(carreira, key, value)
        session.commit()
        session.refresh(carreira)
        return CarreiraOut.model_validate(carreira) # Retorna a carreira atualizada como schema de saída
    return None

# DELETE / DELETE - Remove uma carreira pelo id
def deletar_carreira(session, id: int) -> CarreiraOut | None:
    carreira = session.query(Carreira).filter(Carreira.id == id).first()  # Busca a carreira pelo id
    if carreira:
        session.delete(carreira)  # Remove do banco
        session.commit()
        return CarreiraOut.model_validate(carreira) # Retorna a carreira removida como schema de saída
    return None
