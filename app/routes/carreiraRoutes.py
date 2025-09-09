
from fastapi import APIRouter, HTTPException, Depends
from app.services.carreira import listar_carreiras, buscar_carreira_por_id, criar_carreira
from app.schemas import CarreiraBase, CarreiraOut
from app.dependencies import pegar_sessao, setup_database
from sqlalchemy.orm import sessionmaker, Session
from app.models import Carreira

carreiraRouter = APIRouter(prefix="/carreira", tags=["carreira"])

@carreiraRouter.get("/")
def get_carreiras():
    return listar_carreiras()


@carreiraRouter.post("/cadastro_carreira")
async def cadastro(carreira_schema: CarreiraBase, session: Session = Depends(pegar_sessao)): # passa como parametro os dados que o usuário vai inserir ao acessar a rota e a sessão do banco de dados
    carreira = session.query(Carreira).filter(Carreira.nome == carreira_schema.nome).first() # verifica se a carreira já existe no banco de dados. (first pega o primeiro resultado que encontrar, se encontrar algum resultado, significa que a carreira já existe)
    if carreira: 
        # se ja existir um usuario com esse email, retorna um erro
        raise HTTPException(status_code=400, detail="Carreira já cadastrada")
    else:
       
        nova_carreira = criar_carreira(session, carreira_schema)
        return {"message": f"Carreira cadastrada com sucesso {nova_carreira.nome}"}
    

@carreiraRouter.get("/{carreira_id}")
def get_carreira(carreira_id: int):
    carreira = buscar_carreira_por_id(carreira_id)
    if not carreira:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    return carreira
