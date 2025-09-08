from app.models import Conhecimento, setup_database # modelo da tabela e conexão com o banco de dados
from app.schemas import ConhecimentoBase, ConhecimentoOut # schema de dados

engine, SessionLocal, Base = setup_database() # configuração do banco de dados

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# CREATE - Cria um novo conhecimento
def criar_conhecimento(session, conhecimento_data: ConhecimentoBase) -> ConhecimentoOut:
    novo_conhecimento = Conhecimento(**conhecimento_data.model_dump()) # Cria um objeto Conhecimento a partir dos dados do schema
    session.add(novo_conhecimento)  # Adiciona no banco
    session.commit() # Salva no banco
    session.refresh(novo_conhecimento) # Atualiza o objeto com dados do banco
    return ConhecimentoOut.model_validate(novo_conhecimento) # Converte o modelo SQLAlchemy para o schema de saída (ConhecimentoOut)

# READ - Lista todos os conhecimentos
def listar_conhecimentos(session) -> list[ConhecimentoOut]:
    conhecimentos = session.query(Conhecimento).all()  # Busca todos os conhecimentos no banco
    return [ConhecimentoOut.model_validate(conhecimento) for conhecimento in conhecimentos] # Converte cada conhecimento para o schema de saída

# READ - Busca um conhecimento pelo id
def buscar_conhecimento_por_id(session, id: int) -> ConhecimentoOut | None:
    conhecimento = session.query(Conhecimento).filter(Conhecimento.id == id).first()  # Busca o conhecimento pelo id
    return ConhecimentoOut.model_validate(conhecimento) if conhecimento else None # Se encontrado converte para schema de saída, senão retorna None

# UPDATE - Atualiza os dados de um conhecimento existente usando schema
def atualizar_conhecimento(session, id: int, conhecimento_data: ConhecimentoBase) -> ConhecimentoOut | None:
    conhecimento = session.query(Conhecimento).filter(Conhecimento.id == id).first()  # Busca o conhecimento pelo id
    if conhecimento:
        # Atualiza os campos do conhecimento com os dados recebidos
        for key, value in conhecimento_data.model_dump(exclude_unset=True).items():
            setattr(conhecimento, key, value)
        session.commit()
        session.refresh(conhecimento)
        return ConhecimentoOut.model_validate(conhecimento) # Retorna o conhecimento atualizado como schema de saída
    return None

# DELETE - Remove um conhecimento pelo id
def deletar_conhecimento(session, id: int) -> ConhecimentoOut | None:
    conhecimento = session.query(Conhecimento).filter(Conhecimento.id == id).first()  # Busca o conhecimento pelo id
    if conhecimento:
        session.delete(conhecimento)  # Remove do banco
        session.commit()
        return ConhecimentoOut.model_validate(conhecimento) # Retorna o conhecimento removido como schema de saída
    return None