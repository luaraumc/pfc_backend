from fastapi import APIRouter, HTTPException, Depends 
from app.services.carreiraHabilidade import listar_carreira_habilidades, remover_carreira_habilidade 
from app.schemas.carreiraHabilidadeSchemas import CarreiraHabilidadeOut 
from app.dependencies import pegar_sessao, requer_admin 
from sqlalchemy.orm import Session 

carreiraHabilidadeRouter = APIRouter(prefix="/carreira", tags=["carreira"])

@carreiraHabilidadeRouter.get("/{carreira_id}/habilidades", response_model=list[CarreiraHabilidadeOut])
async def listar_habilidades_carreira_route(
    carreira_id: int,
    session: Session = Depends(pegar_sessao)
):
    """Lista todas as habilidades associadas a uma carreira específica"""
    return listar_carreira_habilidades(session, carreira_id)

@carreiraHabilidadeRouter.delete("/{carreira_id}/remover-habilidade/{habilidade_id}", response_model=CarreiraHabilidadeOut)
async def remover_habilidade_carreira_route(
    carreira_id: int,
    habilidade_id: int,
    usuario: dict = Depends(requer_admin), 
    session: Session = Depends(pegar_sessao)
):
    """Remove a associação entre uma carreira e uma habilidade específica, disponível apenas para administradores"""
    resultado = remover_carreira_habilidade(session, carreira_id, habilidade_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Relação carreira-habilidade não encontrada")
    return resultado
