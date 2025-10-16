from fastapi import APIRouter, Depends, HTTPException # cria dependências e exceções HTTP
from sqlalchemy.orm import Session # cria sessões com o banco de dados
from app.schemas import HabilidadeBase, HabilidadeOut  # <- importe HabilidadeBase
from app.services.habilidade import listar_habilidades, buscar_habilidade_por_id, atualizar_habilidade, deletar_habilidade # serviços relacionados a habilidade
from app.dependencies import pegar_sessao, requer_admin

# Inicializa o router
habilidadeRouter = APIRouter(prefix="/habilidade", tags=["habilidade"])

# Listar todas as habilidades
@habilidadeRouter.get("/", response_model=list[HabilidadeOut])
def listar(session: Session = Depends(pegar_sessao)):
	return listar_habilidades(session)

# Buscar habilidade por ID
@habilidadeRouter.get("/{habilidade_id}", response_model=HabilidadeOut)
def buscar(habilidade_id: int, session: Session = Depends(pegar_sessao)):
	habilidade = buscar_habilidade_por_id(session, habilidade_id)
	if not habilidade:
		raise HTTPException(status_code=404, detail="Habilidade não encontrada")
	return habilidade

# Atualizar habilidade - AUTENTICADA
@habilidadeRouter.put("/atualizar/{habilidade_id}", response_model=HabilidadeOut)
def atualizar(
	habilidade_id: int,
	habilidade_data: HabilidadeBase,  # <- use o schema de entrada
	usuario: dict = Depends(requer_admin),
	session: Session = Depends(pegar_sessao),
):
	habilidade = atualizar_habilidade(session, habilidade_id, habilidade_data)
	if not habilidade:
		raise HTTPException(status_code=404, detail="Habilidade não encontrada")
	return habilidade

# Deletar habilidade - AUTENTICADA
@habilidadeRouter.delete("/deletar/{habilidade_id}")
def deletar(
	habilidade_id: int,
	usuario: dict = Depends(requer_admin),
	session: Session = Depends(pegar_sessao),
):
	habilidade = deletar_habilidade(session, habilidade_id)
	if not habilidade:
		raise HTTPException(status_code=404, detail="Habilidade não encontrada")
	return {"message": f"Habilidade '{habilidade.nome}' deletada com sucesso"}
