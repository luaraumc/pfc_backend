from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.conhecimentoSchemas import ConhecimentoBase, ConhecimentoOut
from app.services.conhecimento import criar_conhecimento, listar_conhecimentos, buscar_conhecimento_por_id , atualizar_conhecimento, deletar_conhecimento
from app.dependencies import pegar_sessao, requer_admin
from app.models.conhecimentoModels import Conhecimento

conhecimentoRouter = APIRouter(prefix="/conhecimento", tags=["conhecimento"])

@conhecimentoRouter.get("/", response_model=list[ConhecimentoOut])
def listar(session: Session = Depends(pegar_sessao)):
	"""Lista todos os conhecimentos cadastrados no sistema"""
	return listar_conhecimentos(session)

@conhecimentoRouter.get("/{conhecimento_id}", response_model=ConhecimentoOut)
def buscar(conhecimento_id: int, session: Session = Depends(pegar_sessao)):
	"""Busca um conhecimento específico pelo ID ou retorna erro 404 se não encontrado"""
	conhecimento = buscar_conhecimento_por_id(session, conhecimento_id)
	if not conhecimento:
		raise HTTPException(status_code=404, detail="Conhecimento não encontrado")
	return conhecimento

@conhecimentoRouter.post("/cadastro")
def cadastrar(
	conhecimento_schema: ConhecimentoBase,
	usuario: dict = Depends(requer_admin),
	session: Session = Depends(pegar_sessao),
):
	"""Cadastra um novo conhecimento verificando duplicatas, disponível apenas para administradores"""
	existe = session.query(Conhecimento).filter(Conhecimento.nome.ilike(conhecimento_schema.nome)).first()
	if existe:
		raise HTTPException(status_code=400, detail="Conhecimento já cadastrado")
	criado = criar_conhecimento(session, conhecimento_schema)
	return {"message": f"Conhecimento '{criado.nome}' cadastrado com sucesso"}

@conhecimentoRouter.put("/atualizar/{conhecimento_id}")
def atualizar(
	conhecimento_id: int,
	conhecimento_schema: ConhecimentoBase,
	usuario: dict = Depends(requer_admin),
	session: Session = Depends(pegar_sessao),
):
	"""Atualiza os dados de um conhecimento existente pelo ID, disponível apenas para administradores"""
	conhecimento = atualizar_conhecimento(session, conhecimento_id, conhecimento_schema)
	if not conhecimento:
		raise HTTPException(status_code=404, detail="Conhecimento não encontrado")
	return {"message": f"Conhecimento '{conhecimento.nome}' atualizado com sucesso"}

@conhecimentoRouter.delete("/deletar/{conhecimento_id}")
def deletar(
	conhecimento_id: int,
	usuario: dict = Depends(requer_admin),
	session: Session = Depends(pegar_sessao),
):
	"""Remove um conhecimento do sistema pelo ID, disponível apenas para administradores"""
	conhecimento = deletar_conhecimento(session, conhecimento_id)
	if not conhecimento:
		raise HTTPException(status_code=404, detail="Conhecimento não encontrado")
	return {"message": f"Conhecimento '{conhecimento.nome}' deletado com sucesso"}
