from app.models import Compatibilidade # modelo de tabela definido no arquivo models.py
from app.models import setup_database # conexão do banco de dados
from app.schemas import CompatibilidadeBase, CompatibilidadeOut # conexão do banco de dados

engine, SessionLocal, Base = setup_database()

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# CREATE - Cria uma nova compatibilidade
def criar_compatibilidade(session, compatibilidade_data: CompatibilidadeBase) -> CompatibilidadeOut:
    nova_compatibilidade = Compatibilidade(**compatibilidade_data.model_dump()) # Cria um objeto Compatibilidade a partir dos dados do schema
    session.add(nova_compatibilidade)  # Adiciona no banco
    session.commit() # Salva no banco
    session.refresh(nova_compatibilidade) # Atualiza o objeto com dados do banco
    return CompatibilidadeOut.model_validate(nova_compatibilidade) # Converte o modelo SQLAlchemy para o schema de saída (CompatibilidadeOut)

# READ - Lista todas as compatibilidades
def listar_compatibilidades(session) -> list[CompatibilidadeOut]:
    compatibilidades = session.query(Compatibilidade).all()  # Busca todas as compatibilidades no banco
    return [CompatibilidadeOut.model_validate(c) for c in compatibilidades] # Converte cada compatibilidade para o schema de saída

# READ - Busca uma compatibilidade pelo id
def buscar_compatibilidade_por_id(session, id: int) -> CompatibilidadeOut | None:
    compatibilidade = session.query(Compatibilidade).filter(Compatibilidade.id == id).first()  # Busca a compatibilidade pelo id
    return CompatibilidadeOut.model_validate(compatibilidade) if compatibilidade else None # Se encontrada converte para schema de saída, senão retorna None

# UPDATE - Atualiza os dados de uma compatibilidade existente usando schema
def atualizar_compatibilidade(session, id: int, compatibilidade_data: CompatibilidadeBase) -> CompatibilidadeOut | None:
    compatibilidade = session.query(Compatibilidade).filter(Compatibilidade.id == id).first()  # Busca a compatibilidade pelo id
    if compatibilidade:
        # Atualiza os campos da compatibilidade com os dados recebidos
        for key, value in compatibilidade_data.model_dump(exclude_unset=True).items():
            setattr(compatibilidade, key, value)
        session.commit()
        session.refresh(compatibilidade)
        return CompatibilidadeOut.model_validate(compatibilidade) # Retorna a compatibilidade atualizada como schema de saída
    return None

# DELETE - Remove uma compatibilidade pelo id
def deletar_compatibilidade(session, id: int) -> CompatibilidadeOut | None:
    compatibilidade = session.query(Compatibilidade).filter(Compatibilidade.id == id).first()  # Busca a compatibilidade pelo id
    if compatibilidade:
        session.delete(compatibilidade)  # Remove do banco
        session.commit()
        return CompatibilidadeOut.model_validate(compatibilidade) # Retorna a compatibilidade removida como schema de saída
