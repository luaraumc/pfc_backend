from app.models import Habilidade # modelo de tabela definido no arquivo models.py
from app.schemas import HabilidadeBase, HabilidadeOut, HabilidadeAtualizar # schema de entrada e saída
from app.models import Categoria

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# READ - Lista todas as habilidades
def listar_habilidades(session) -> list[HabilidadeOut]:
    habilidades = session.query(Habilidade).all()  # Busca todas as habilidades no banco
    return [HabilidadeOut.model_validate(habilidade) for habilidade in habilidades] # Converte cada habilidade para o schema de saída

# READ - Busca uma habilidade pelo id
def buscar_habilidade_por_id(session, id: int) -> HabilidadeOut | None:
    habilidade = session.query(Habilidade).filter(Habilidade.id == id).first()  # Busca a habilidade pelo id
    return HabilidadeOut.model_validate(habilidade) if habilidade else None # Se encontrada converte para schema de saída, senão retorna None

# UPDATE / PUT - Atualiza os dados de uma habilidade existente usando schema
def atualizar_habilidade(session, id: int, habilidade_data: HabilidadeAtualizar) -> HabilidadeOut | None:
    habilidade = session.query(Habilidade).filter(Habilidade.id == id).first()  # Busca a habilidade pelo id
    if habilidade:
        # Atualiza os campos da habilidade com os dados recebidos
        data = habilidade_data.model_dump(exclude_unset=True)
        # Atualiza nome (se enviado)
        nome = data.get('nome')
        if isinstance(nome, str) and nome.strip():
            habilidade.nome = nome.strip()
        # Atualiza categoria (se enviado)
        cat_id = data.get('categoria_id')
        if cat_id is not None:
            categoria = session.query(Categoria).filter(Categoria.id == cat_id).first()
            if not categoria:
                return None
            habilidade.categoria_id = categoria.id
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
