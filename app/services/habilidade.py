
from app.models import Habilidade # modelo de tabela definido no arquivo models.py
from app.models import setup_database # conexão do banco de dados
from app.schemas import HabilidadeBase, HabilidadeOut # conexão do banco de dados

engine, SessionLocal, Base = setup_database() # configuração do banco de dados

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# CREATE - Cria uma nova habilidade
def criar_habilidade(session, habilidade_data: HabilidadeBase) -> HabilidadeOut:
    nova_habilidade = Habilidade(**habilidade_data.model_dump()) # Cria um objeto Habilidade a partir dos dados do schema
    session.add(nova_habilidade)  # Adiciona no banco
    session.commit() # Salva no banco
    session.refresh(nova_habilidade) # Atualiza o objeto com dados do banco
    return HabilidadeOut.model_validate(nova_habilidade) # Converte o modelo SQLAlchemy para o schema de saída (HabilidadeOut)

# READ - Lista todas as habilidades
def listar_habilidades(session) -> list[HabilidadeOut]:
    habilidades = session.query(Habilidade).all()  # Busca todas as habilidades no banco
    return [HabilidadeOut.model_validate(habilidade) for habilidade in habilidades] # Converte cada habilidade para o schema de saída

# READ - Busca uma habilidade pelo id
def buscar_habilidade_por_id(session, id: int) -> HabilidadeOut | None:
    habilidade = session.query(Habilidade).filter(Habilidade.id == id).first()  # Busca a habilidade pelo id
    return HabilidadeOut.model_validate(habilidade) if habilidade else None # Se encontrada converte para schema de saída, senão retorna None

# UPDATE - Atualiza os dados de uma habilidade existente usando schema
def atualizar_habilidade(session, id: int, habilidade_data: HabilidadeBase) -> HabilidadeOut | None:
    habilidade = session.query(Habilidade).filter(Habilidade.id == id).first()  # Busca a habilidade pelo id
    if habilidade:
        # Atualiza os campos da habilidade com os dados recebidos
        for key, value in habilidade_data.model_dump(exclude_unset=True).items():
            setattr(habilidade, key, value)
        session.commit()
        session.refresh(habilidade)
        return HabilidadeOut.model_validate(habilidade) # Retorna a habilidade atualizada como schema de saída
    return None

# DELETE - Remove uma habilidade pelo id
def deletar_habilidade(session, id: int) -> HabilidadeOut | None:
    habilidade = session.query(Habilidade).filter(Habilidade.id == id).first()  # Busca a habilidade pelo id
    if habilidade:
        session.delete(habilidade)  # Remove do banco
        session.commit()
        return HabilidadeOut.model_validate(habilidade) # Retorna a habilidade removida como schema de saída
    return None