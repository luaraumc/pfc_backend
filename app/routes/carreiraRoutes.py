from fastapi import APIRouter, HTTPException, Depends
from app.services.carreira import criar_carreira, listar_carreiras, buscar_carreira_por_id, atualizar_carreira, deletar_carreira
from app.schemas import CarreiraBase, CarreiraOut
from app.dependencies import pegar_sessao
from sqlalchemy.orm import Session
from app.models import Carreira

carreiraRouter = APIRouter(prefix="/carreira", tags=["carreira"])

# Listar todas as carreiras
@carreiraRouter.get("/", response_model=list[CarreiraOut]) # response_model: validar e filtrar os dados antes de enviar ao cliente
async def get_carreiras(session: Session = Depends(pegar_sessao)):
    return listar_carreiras(session)

# Buscar carreira por ID
@carreiraRouter.get("/{carreira_id}", response_model=CarreiraOut) # response_model: validar e filtrar os dados antes de enviar ao cliente
async def get_carreira(carreira_id: int, session: Session = Depends(pegar_sessao)):
    carreira = buscar_carreira_por_id(session, carreira_id)
    if not carreira:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    return carreira

# Cadastrar carreira
@carreiraRouter.post("/cadastro")
async def cadastro(carreira_schema: CarreiraBase, session: Session = Depends(pegar_sessao)): # passa como parametro os dados que o usuário tem que inserir ao acessar a rota e a sessão do banco de dados
    carreira = session.query(Carreira).filter(Carreira.nome == carreira_schema.nome).first() # verifica se a carreira já existe no banco de dados. (first pega o primeiro resultado que encontrar, se encontrar algum resultado, significa que a carreira já existe)
    if carreira: 
        raise HTTPException(status_code=400, detail="Carreira já cadastrada") # se ja existir uma carreira com esse nome, retorna um erro
    else:
       
        nova_carreira = criar_carreira(session, carreira_schema)
        return {"message": f"Carreira cadastrada com sucesso: {nova_carreira.nome}"}

# Atualizar carreira
@carreiraRouter.put("/atualizar/{carreira_id}")
async def atualizar(carreira_id: int, carreira_schema: CarreiraBase, session: Session = Depends(pegar_sessao)):
    carreira = atualizar_carreira(session, carreira_id, carreira_schema)
    if not carreira:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    return {"message": f"Carreira atualizada com sucesso: {carreira.nome}"}

# Deletar carreira
@carreiraRouter.delete("/deletar/{carreira_id}")
async def deletar(carreira_id: int, session: Session = Depends(pegar_sessao)):
    carreira = deletar_carreira(session, carreira_id)
    if not carreira:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    return {"message": f"Carreira deletada com sucesso: {carreira.nome}"}
