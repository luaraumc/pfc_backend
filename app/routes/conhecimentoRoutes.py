from fastapi import APIRouter, Depends, HTTPException # cria dependências e exceções HTTP
from sqlalchemy.orm import Session # cria sessões com o banco de dados
from app.schemas import ConhecimentoBase, ConhecimentoOut # schemas para validação de dados
from app.services.conhecimento import criar_conhecimento, listar_conhecimentos, buscar_conhecimento_por_id , atualizar_conhecimento, deletar_conhecimento # serviços relacionados a conhecimento
from app.dependencies import pegar_sessao, requer_admin # pegar a sessão do banco de dados, verificar o token e requerer admin

# Inicializa o router
conhecimentoRouter = APIRouter(prefix="/conhecimento", tags=["conhecimento"])

# Listar todos os conhecimentos
@conhecimentoRouter.get("/", response_model=list[ConhecimentoOut])
def listar(session: Session = Depends(pegar_sessao)):
	return listar_conhecimentos(session)

# Buscar conhecimento por ID
@conhecimentoRouter.get("/{conhecimento_id}", response_model=ConhecimentoOut)
def buscar(conhecimento_id: int, session: Session = Depends(pegar_sessao)):
	conhecimento = buscar_conhecimento_por_id(session, conhecimento_id)
	if not conhecimento:
		raise HTTPException(status_code=404, detail="Conhecimento não encontrado")
	return conhecimento

# Cadastrar conhecimento - AUTENTICADA
@conhecimentoRouter.post("/cadastro")
def cadastrar(
	conhecimento_schema: ConhecimentoBase,
	usuario: dict = Depends(requer_admin),
	session: Session = Depends(pegar_sessao),
):
	from app.models import Conhecimento
	existe = session.query(Conhecimento).filter(Conhecimento.nome.ilike(conhecimento_schema.nome)).first()
	if existe:
		raise HTTPException(status_code=400, detail="Conhecimento já cadastrado")
	criado = criar_conhecimento(session, conhecimento_schema)
	return {"message": f"Conhecimento '{criado.nome}' cadastrado com sucesso"}

# Atualizar conhecimento - AUTENTICADA
@conhecimentoRouter.put("/atualizar/{conhecimento_id}")
def atualizar(
	conhecimento_id: int, # ID do conhecimento a ser atualizado
	conhecimento_schema: ConhecimentoBase, # passa como parametro os dados que o usuário tem que inserir ao acessar a rota
	usuario: dict = Depends(requer_admin), # verifica se é um usuário permitido (admin)
	session: Session = Depends(pegar_sessao), # pega a sessão do banco de dados
):
	conhecimento = atualizar_conhecimento(session, conhecimento_id, conhecimento_schema) # chama a função de serviço para atualizar o conhecimento
	if not conhecimento:
		raise HTTPException(status_code=404, detail="Conhecimento não encontrado")
	return {"message": f"Conhecimento '{conhecimento.nome}' atualizado com sucesso"}

# Deletar conhecimento - AUTENTICADA
@conhecimentoRouter.delete("/deletar/{conhecimento_id}")
def deletar(
	conhecimento_id: int,
	usuario: dict = Depends(requer_admin),
	session: Session = Depends(pegar_sessao),
):
	conhecimento = deletar_conhecimento(session, conhecimento_id)
	if not conhecimento:
		raise HTTPException(status_code=404, detail="Conhecimento não encontrado")
	return {"message": f"Conhecimento '{conhecimento.nome}' deletado com sucesso"}
