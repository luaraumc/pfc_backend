from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.vagaSchemas import VagaBase, VagaOut
from app.services.vaga import listar_vagas, criar_vaga, extrair_habilidades_vaga, confirmar_habilidades_vaga, remover_relacao_vaga_habilidade, excluir_vaga_decrementando
from app.dependencies import pegar_sessao, requer_admin


vagaRouter = APIRouter(prefix="/vaga", tags=["vaga"])


@vagaRouter.get("/", response_model=list[VagaOut])
async def get_vagas(session: Session = Depends(pegar_sessao)):
    """Lista todas as vagas cadastradas no sistema ordenadas por data de criação"""
    return listar_vagas(session)


@vagaRouter.post("/cadastro", response_model=VagaOut)
async def criar_vaga_endpoint(
    payload: VagaBase,
    sessao: Session = Depends(pegar_sessao),
    admin=Depends(requer_admin)
):
    """Cadastra uma nova vaga padronizando a descrição sem processar habilidades, disponível apenas para administradores"""
    try:
        return criar_vaga(sessao, payload)
    except ValueError as e:
        if str(e) == "DUPLICATE_VAGA_DESCRICAO":
            raise HTTPException(status_code=409, detail="Já existe uma vaga com a mesma descrição.")
        raise


@vagaRouter.get("/{vaga_id}/preview-habilidades", response_model=list[dict])
async def preview_habilidades_endpoint(
    vaga_id: int,
    sessao: Session = Depends(pegar_sessao),
    admin=Depends(requer_admin)
):
    """Extrai habilidades da descrição da vaga usando IA e retorna preview para edição, disponível apenas para administradores"""
    return extrair_habilidades_vaga(sessao, vaga_id)


@vagaRouter.post("/{vaga_id}/confirmar-habilidades")
async def confirmar_habilidades_endpoint(
    vaga_id: int,
    payload: dict,
    sessao: Session = Depends(pegar_sessao),
    admin=Depends(requer_admin)
):
    """Confirma habilidades editadas e as associa à vaga e carreira, disponível apenas para administradores"""
    habilidades = payload.get("habilidades", []) if isinstance(payload, dict) else []
    try:
        return confirmar_habilidades_vaga(sessao, vaga_id, habilidades)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@vagaRouter.delete("/{vaga_id}/habilidades/{habilidade_id}")
async def remover_relacao_vaga_habilidade_endpoint(
    vaga_id: int,
    habilidade_id: int,
    usuario=Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    """Remove a associação entre uma vaga e uma habilidade específica, disponível apenas para administradores"""
    ok = remover_relacao_vaga_habilidade(session, vaga_id, habilidade_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Relação não encontrada")
    return {"status": "removido"}


@vagaRouter.delete("/{vaga_id}")
async def excluir_vaga_endpoint(
    vaga_id: int,
    sessao: Session = Depends(pegar_sessao),
    admin=Depends(requer_admin)
):
    """Exclui uma vaga e ajusta frequências das habilidades na carreira, disponível apenas para administradores"""
    ok = excluir_vaga_decrementando(sessao, vaga_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    return {"status": "excluida", "vaga_id": vaga_id}
