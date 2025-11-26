from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.mapeamentoSchemas import MapaOut
from app.dependencies import pegar_sessao
from app.services.mapeamento import montar_mapa


mapeamentoRouter = APIRouter(prefix="/mapa", tags=["mapeamento"])


@mapeamentoRouter.get("/", response_model=MapaOut)
def obter_mapa(session: Session = Depends(pegar_sessao)):
    """Retorna o mapa completo de relacionamento entre cursos e carreiras do sistema"""
    dados = montar_mapa(session=session)
    return dados
