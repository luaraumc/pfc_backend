from fastapi import APIRouter, Depends, HTTPException # cria dependências e exceções HTTP
from sqlalchemy.orm import Session # pegar a sessão do banco de dados
from app.schemas import VagaBase, VagaOut # schemas para validação de dados
from app.services.vaga import criar_vaga, listar_vagas, sugerir_carreira_por_titulo # serviços relacionados a vaga
from app.dependencies import pegar_sessao, requer_admin # cria sessões com o banco de dados, verifica o token e requer admin
from app.models import Vaga, Habilidade # adiciona Habilidade para listagem

# Inicializa o router
vagaRouter = APIRouter(prefix="/vaga", tags=["vaga"])

# Listar todas as vagas
@vagaRouter.get("/", response_model=list[VagaOut])
async def get_vagas(session: Session = Depends(pegar_sessao)):
    return listar_vagas(session)

# Cadastrar vaga - AUTENTICADA
@vagaRouter.post("/vaga/cadastro", response_model=VagaOut)
def criar_vaga(
    payload: VagaBase,
    sessao: Session = Depends(pegar_sessao),
    admin=Depends(requer_admin)
):
    from app.models import Vaga, Carreira
    vaga = Vaga(titulo=payload.titulo, descricao=payload.descricao, carreira_id=payload.carreira_id)
    sessao.add(vaga)
    sessao.commit()
    sessao.refresh(vaga)
    if payload.carreira_id is None:
        sugerida = sugerir_carreira_por_titulo(payload.titulo, sessao)
        if sugerida:
            vaga.carreira_id = sugerida
    return VagaOut(
        id=vaga.id,
        titulo=vaga.titulo,
        descricao=vaga.descricao,
        carreira_id=vaga.carreira_id,
        carreira_nome=vaga.carreira.nome if vaga.carreira else None
    )

# Extrair habilidades da vaga - AUTENTICADA (somente admin)
@vagaRouter.post("/{vaga_id}/extrair-habilidades")
async def extrair_habilidades_endpoint(
    vaga_id: int,
    criar_habilidades: bool = True,
    forcar_extracao: bool = False,
    usuario = Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    from app.services.extracao import extrair_habilidades_vaga
    resultado = extrair_habilidades_vaga(session, vaga_id, criar_habilidades=criar_habilidades, forcar_extracao=forcar_extracao)
    if "erro" in resultado:
        raise HTTPException(status_code=404, detail=resultado["erro"])
    return resultado

# Listar habilidades associadas a uma vaga (cache)
@vagaRouter.get("/{vaga_id}/habilidades", response_model=list)
async def listar_habilidades_vaga(
    vaga_id: int,
    session: Session = Depends(pegar_sessao)
):
    from app.services.vagaHabilidade import listar_habilidades_por_vaga
    habilidades = listar_habilidades_por_vaga(session, vaga_id)
    return [h.nome for h in habilidades]

# Remover relação vaga-habilidade (admin)
@vagaRouter.delete("/{vaga_id}/habilidades/{habilidade_id}")
async def remover_relacao_vaga_habilidade_endpoint(
    vaga_id: int,
    habilidade_id: int,
    usuario = Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    from app.services.vagaHabilidade import remover_relacao_vaga_habilidade
    ok = remover_relacao_vaga_habilidade(session, vaga_id, habilidade_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Relação não encontrada")
    return {"status": "removido"}
