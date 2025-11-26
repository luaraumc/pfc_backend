from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.habilidadeSchemas import HabilidadeOut, HabilidadeAtualizar
from app.models.categoriaModels import Categoria
from app.services.habilidade import listar_habilidades, buscar_habilidade_por_id, atualizar_habilidade, deletar_habilidade
from app.dependencies import pegar_sessao, requer_admin


habilidadeRouter = APIRouter(prefix="/habilidade", tags=["habilidade"])


@habilidadeRouter.get("/", response_model=list[HabilidadeOut])
def listar(session: Session = Depends(pegar_sessao)):
	"""Lista todas as habilidades cadastradas no sistema"""
	return listar_habilidades(session)


@habilidadeRouter.get("/categorias", response_model=list[dict])
def listar_categorias(session: Session = Depends(pegar_sessao)):
	"""Lista todas as categorias disponíveis ordenadas alfabeticamente"""
	categorias = session.query(Categoria).order_by(Categoria.nome.asc()).all()
	return [{"id": c.id, "nome": c.nome} for c in categorias]


@habilidadeRouter.get("/{habilidade_id}", response_model=HabilidadeOut)
def buscar(habilidade_id: int, session: Session = Depends(pegar_sessao)):
	"""Busca uma habilidade específica pelo ID ou retorna erro 404 se não encontrada"""
	habilidade = buscar_habilidade_por_id(session, habilidade_id)
	if not habilidade:
		raise HTTPException(status_code=404, detail="Habilidade não encontrada")
	return habilidade


@habilidadeRouter.put("/atualizar/{habilidade_id}", response_model=HabilidadeOut)
def atualizar(
	habilidade_id: int,
	habilidade_data: HabilidadeAtualizar,
	usuario: dict = Depends(requer_admin),
	session: Session = Depends(pegar_sessao),
):
	"""Atualiza nome e/ou categoria de uma habilidade existente, disponível apenas para administradores"""
	habilidade = atualizar_habilidade(session, habilidade_id, habilidade_data)
	if not habilidade:
		raise HTTPException(status_code=404, detail="Habilidade não encontrada")
	return habilidade


@habilidadeRouter.delete("/deletar/{habilidade_id}")
def deletar(
	habilidade_id: int,
	usuario: dict = Depends(requer_admin),
	session: Session = Depends(pegar_sessao),
):
	"""Remove uma habilidade do sistema pelo ID, disponível apenas para administradores"""
	habilidade = deletar_habilidade(session, habilidade_id)
	if not habilidade:
		raise HTTPException(status_code=404, detail="Habilidade não encontrada")
	return {"message": f"Habilidade '{habilidade.nome}' deletada com sucesso"}
