from fastapi import APIRouter, Depends, HTTPException # cria dependências e exceções HTTP
from sqlalchemy.orm import Session # pegar a sessão do banco de dados
from app.schemas.vagaSchemas import VagaBase, VagaOut
from app.services.vaga import listar_vagas, criar_vaga, extrair_habilidades_vaga, confirmar_habilidades_vaga, remover_relacao_vaga_habilidade, excluir_vaga_decrementando # serviços relacionados à vaga
from app.dependencies import pegar_sessao, requer_admin # cria sessões com o banco de dados, verifica o token e requer admin

# Inicializa o router
vagaRouter = APIRouter(prefix="/vaga", tags=["vaga"])

# Listar todas as vagas
@vagaRouter.get("/", response_model=list[VagaOut])
async def get_vagas(session: Session = Depends(pegar_sessao)):
    return listar_vagas(session)

# Cadastrar vaga (sem processar habilidades) - AUTENTICADA
@vagaRouter.post("/cadastro", response_model=VagaOut)
async def criar_vaga_endpoint(
    payload: VagaBase,
    sessao: Session = Depends(pegar_sessao),
    admin=Depends(requer_admin)
):
    try:
        return criar_vaga(sessao, payload)
    except ValueError as e:
        if str(e) == "DUPLICATE_VAGA_DESCRICAO":
            raise HTTPException(status_code=409, detail="Já existe uma vaga com a mesma descrição.")
        raise

# Pré-visualização de habilidades extraídas - AUTENTICADA
# Retorna lista de objetos com chaves: nome, habilidade_id, categoria_sugerida, categoria_id, categoria_nome
@vagaRouter.get("/{vaga_id}/preview-habilidades", response_model=list[dict])
async def preview_habilidades_endpoint(
    vaga_id: int,
    sessao: Session = Depends(pegar_sessao),
    admin=Depends(requer_admin)
):
    return extrair_habilidades_vaga(sessao, vaga_id)

# Confirmação das habilidades editadas - AUTENTICADA
@vagaRouter.post("/{vaga_id}/confirmar-habilidades")
async def confirmar_habilidades_endpoint(
    vaga_id: int,
    payload: dict,
    sessao: Session = Depends(pegar_sessao),
    admin=Depends(requer_admin)
):
    habilidades = payload.get("habilidades", []) if isinstance(payload, dict) else []
    try:
        return confirmar_habilidades_vaga(sessao, vaga_id, habilidades)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Remover relação vaga-habilidade - AUTENTICADA
@vagaRouter.delete("/{vaga_id}/habilidades/{habilidade_id}")
async def remover_relacao_vaga_habilidade_endpoint(
    vaga_id: int,
    habilidade_id: int,
    usuario=Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    ok = remover_relacao_vaga_habilidade(session, vaga_id, habilidade_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Relação não encontrada")
    return {"status": "removido"}

# Deletar vaga - AUTENTICADA
@vagaRouter.delete("/{vaga_id}")
async def excluir_vaga_endpoint(
    vaga_id: int,
    sessao: Session = Depends(pegar_sessao),
    admin=Depends(requer_admin)
):
    ok = excluir_vaga_decrementando(sessao, vaga_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    return {"status": "excluida", "vaga_id": vaga_id}
