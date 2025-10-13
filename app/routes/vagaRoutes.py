from fastapi import APIRouter, Depends, HTTPException # cria dependências e exceções HTTP
from sqlalchemy.orm import Session # pegar a sessão do banco de dados
from app.schemas import VagaBase, VagaOut,VagaCompletaOut # schemas para validação de dados
from app.services.vaga import criar_vaga, listar_vagas, sugerir_carreira_por_titulo # serviços relacionados a vaga
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

# Remover relação vaga-habilidade (admin)
@vagaRouter.delete("/{vaga_id}/habilidades/{habilidade_id}")
async def remover_relacao_vaga_habilidade_endpoint(
    vaga_id: int,
    habilidade_id: int,
    usuario=Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    from app.services.vagaHabilidade import remover_relacao_vaga_habilidade
    ok = remover_relacao_vaga_habilidade(session, vaga_id, habilidade_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Relação não encontrada")
    return {"status": "removido"}
