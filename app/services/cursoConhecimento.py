from app.models.cursoConhecimentoModels import CursoConhecimento
from app.schemas.cursoConhecimentoSchemas import CursoConhecimentoBase, CursoConhecimentoOut

def criar_curso_conhecimento(session, curso_conhecimento_data: CursoConhecimentoBase) -> CursoConhecimentoOut:
    """Cria uma nova associação entre curso e conhecimento no banco de dados e retorna como CursoConhecimentoOut"""
    nova = CursoConhecimento(**curso_conhecimento_data.model_dump())
    session.add(nova)
    session.commit()
    session.refresh(nova)
    return CursoConhecimentoOut.model_validate(nova)

def listar_curso_conhecimentos(session, curso_id: int) -> list[CursoConhecimentoOut]:
    """Lista todos os conhecimentos associados a um curso específico e retorna como lista de CursoConhecimentoOut"""
    conhecimentos = session.query(CursoConhecimento).filter_by(curso_id=curso_id).all()
    return [CursoConhecimentoOut.model_validate(c) for c in conhecimentos]

def remover_curso_conhecimento(session, curso_id: int, conhecimento_id: int) -> CursoConhecimentoOut | None:
    """Remove a associação entre um curso e um conhecimento específico e retorna os dados removidos ou None se não encontrada"""
    relacao = session.query(CursoConhecimento).filter_by(curso_id=curso_id, conhecimento_id=conhecimento_id).first()
    if relacao:
        session.delete(relacao)
        session.commit()
        return CursoConhecimentoOut.model_validate(relacao)
    return None
