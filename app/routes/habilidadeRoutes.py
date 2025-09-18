from fastapi import APIRouter, Depends, HTTPException # cria dependências e exceções HTTP
from sqlalchemy.orm import Session # cria sessões com o banco de dados
from app.schemas import HabilidadeBase, HabilidadeOut # schemas para validação de dados
from app.services.habilidade import criar_habilidade, listar_habilidades, deletar_habilidade # serviços relacionados a habilidade
from app.dependencies import pegar_sessao, requer_admin

# Inicializa o router
habilidadeRouter = APIRouter(prefix="/habilidade", tags=["habilidade"])

# Listar todas as habilidades
@habilidadeRouter.get("/", response_model=list[HabilidadeOut])
def listar(session: Session = Depends(pegar_sessao)):
	return listar_habilidades(session)

# Cadastrar habilidade - AUTENTICADA
@habilidadeRouter.post("/cadastro")
def cadastrar(
	habilidade_schema: HabilidadeBase,
	usuario: dict = Depends(requer_admin),
	session: Session = Depends(pegar_sessao),
):
	from app.models import Habilidade
	existe = session.query(Habilidade).filter(Habilidade.nome.ilike(habilidade_schema.nome)).first()
	if existe:
		raise HTTPException(status_code=400, detail="Habilidade já cadastrada")
	criada = criar_habilidade(session, habilidade_schema)
	return {"message": f"Habilidade '{criada.nome}' cadastrada com sucesso"}

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
