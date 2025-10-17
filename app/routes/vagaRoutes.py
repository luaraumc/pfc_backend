from fastapi import APIRouter, Depends, HTTPException # cria dependências e exceções HTTP
from sqlalchemy.orm import Session # pegar a sessão do banco de dados
from app.schemas import VagaBase, VagaOut,VagaCompletaOut # schemas para validação de dados
from app.services.vaga import criar_vaga, listar_vagas, criar_vaga_basica, extrair_habilidades_vaga, confirmar_habilidades_vaga # serviços relacionados a vaga
from app.dependencies import pegar_sessao, requer_admin # cria sessões com o banco de dados, verifica o token e requer admin

# Inicializa o router
vagaRouter = APIRouter(prefix="/vaga", tags=["vaga"])

# Listar todas as vagas
@vagaRouter.get("/", response_model=list[VagaOut])
async def get_vagas(session: Session = Depends(pegar_sessao)):
    return listar_vagas(session)

# Cadastrar vaga - AUTENTICADA
@vagaRouter.post("/cadastro", response_model=VagaCompletaOut)
async def criar_vaga_endpoint(
    payload: VagaBase,
    sessao: Session = Depends(pegar_sessao),
    admin=Depends(requer_admin)
):
    """
    Cria uma vaga, extrai habilidades automaticamente e associa à carreira.
    Retorna:
    {
        "titulo": str,
        "carreira_id": int,
        "habilidades_extraidas": list[str],
        "habilidades_criadas": list[str],
        "habilidades_ja_existiam": list[str]
    }
    """
    return criar_vaga(sessao, payload)

# Cadastrar vaga (básico, sem salvar habilidades) - AUTENTICADA
@vagaRouter.post("/cadastro-basico", response_model=VagaOut)
async def criar_vaga_basico_endpoint(
    payload: VagaBase,
    sessao: Session = Depends(pegar_sessao),
    admin=Depends(requer_admin)
):
    return criar_vaga_basica(sessao, payload)

# Pré-visualizar habilidades extraídas (não persiste) - AUTENTICADA
@vagaRouter.get("/{vaga_id}/preview-habilidades", response_model=list[str])
async def preview_habilidades_endpoint(
    vaga_id: int,
    sessao: Session = Depends(pegar_sessao),
    admin=Depends(requer_admin)
):
    return extrair_habilidades_vaga(sessao, vaga_id)

# Confirmar habilidades finais para a vaga - AUTENTICADA
@vagaRouter.post("/{vaga_id}/confirmar-habilidades")
async def confirmar_habilidades_endpoint(
    vaga_id: int,
    body: dict,
    sessao: Session = Depends(pegar_sessao),
    admin=Depends(requer_admin)
):
    habilidades = body.get("habilidades") or []
    if not isinstance(habilidades, list):
        raise HTTPException(status_code=400, detail="Campo 'habilidades' deve ser uma lista")
    try:
        return confirmar_habilidades_vaga(sessao, vaga_id, habilidades)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# Remover relação vaga-habilidade (admin)
@vagaRouter.delete("/{vaga_id}/habilidades/{habilidade_id}")
async def remover_relacao_vaga_habilidade_endpoint(
    vaga_id: int,
    habilidade_id: int,
    usuario=Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    from app.services.vaga import remover_relacao_vaga_habilidade
    ok = remover_relacao_vaga_habilidade(session, vaga_id, habilidade_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Relação não encontrada")
    return {"status": "removido"}
