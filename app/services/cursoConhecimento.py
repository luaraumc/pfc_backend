from app.models.rel_curso_conhecimento import CursoConhecimento # modelo de tabela 
from app.schemas import CursoConhecimentoBase, CursoConhecimentoOut # schema de entrada e saída

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# CREATE / POST - Cria uma nova relação entre curso e conhecimento
def criar_curso_conhecimento(session, curso_conhecimento_data: CursoConhecimentoBase) -> CursoConhecimentoOut:
    nova = CursoConhecimento(**curso_conhecimento_data.model_dump())
    session.add(nova)
    session.commit()
    session.refresh(nova)
    return CursoConhecimentoOut.model_validate(nova)

# READ / GET - Lista todos os conhecimentos do curso
def listar_curso_conhecimentos(session, curso_id: int) -> list[CursoConhecimentoOut]:
    conhecimentos = session.query(CursoConhecimento).filter_by(curso_id=curso_id).all()
    return [CursoConhecimentoOut.model_validate(c) for c in conhecimentos]

# DELETE / DELETE - Remove um conhecimento do curso
def remover_curso_conhecimento(session, curso_id: int, conhecimento_id: int) -> CursoConhecimentoOut | None:
    relacao = session.query(CursoConhecimento).filter_by(curso_id=curso_id, conhecimento_id=conhecimento_id).first()
    if relacao:
        session.delete(relacao)
        session.commit()
        return CursoConhecimentoOut.model_validate(relacao)
    return None
