from fastapi import APIRouter, HTTPException, Depends
from app.services.cursoConhecimento import criar_curso_conhecimento, listar_curso_conhecimentos, remover_curso_conhecimento
from app.schemas.cursoConhecimentoSchemas import CursoConhecimentoBase, CursoConhecimentoOut
from sqlalchemy.orm import Session
from app.dependencies import pegar_sessao, requer_admin
from app.models.cursoConhecimentoModels import CursoConhecimento


cursoConhecimentoRouter = APIRouter(prefix="/curso", tags=["curso"])


@cursoConhecimentoRouter.get("/{curso_id}/conhecimentos", response_model=list[CursoConhecimentoOut])
async def listar_conhecimentos_curso_route(
    curso_id: int,
    session: Session = Depends(pegar_sessao)
):
    """Lista todos os conhecimentos associados a um curso específico"""
    return listar_curso_conhecimentos(session, curso_id)


@cursoConhecimentoRouter.post("/{curso_id}/adicionar-conhecimento/{conhecimento_id}", response_model=CursoConhecimentoOut)
async def adicionar_conhecimento_curso_route(
    curso_id: int,
    conhecimento_id: int,
    usuario: dict = Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    """Adiciona um conhecimento a um curso verificando duplicatas, disponível apenas para administradores"""
    existe = session.query(CursoConhecimento).filter_by(curso_id=curso_id, conhecimento_id=conhecimento_id).first()
    if existe:
        raise HTTPException(status_code=400, detail="Conhecimento já adicionado ao curso")
    curso_conhecimento_data = CursoConhecimentoBase(curso_id=curso_id, conhecimento_id=conhecimento_id)
    return criar_curso_conhecimento(session, curso_conhecimento_data)


@cursoConhecimentoRouter.delete("/{curso_id}/remover-conhecimento/{conhecimento_id}", response_model=CursoConhecimentoOut)
async def remover_conhecimento_curso_route(
    curso_id: int,
    conhecimento_id: int,
    usuario: dict = Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    """Remove a associação entre um curso e um conhecimento específico, disponível apenas para administradores"""
    resultado = remover_curso_conhecimento(session, curso_id, conhecimento_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Relação curso-conhecimento não encontrada")
    return resultado
