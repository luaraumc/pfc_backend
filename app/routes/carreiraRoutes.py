from fastapi import APIRouter, HTTPException, Depends 
from app.services.carreira import criar_carreira, listar_carreiras, buscar_carreira_por_id, atualizar_carreira, deletar_carreira 
from app.schemas.carreiraSchemas import CarreiraBase, CarreiraOut 
from app.dependencies import pegar_sessao, requer_admin 
from sqlalchemy.orm import Session 
from app.models.carreiraModels import Carreira 


carreiraRouter = APIRouter(prefix="/carreira", tags=["carreira"])


@carreiraRouter.get("/", response_model=list[CarreiraOut]) 
async def get_carreiras(session: Session = Depends(pegar_sessao)):
    """Retorna uma lista de todas as carreiras cadastradas no sistema"""
    return listar_carreiras(session)


@carreiraRouter.get("/{carreira_id}", response_model=CarreiraOut) 
async def get_carreira(carreira_id: int, session: Session = Depends(pegar_sessao)):
    """Retorna os detalhes de uma carreira específica pelo ID"""
    carreira = buscar_carreira_por_id(session, carreira_id)
    if not carreira:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    return carreira


@carreiraRouter.post("/cadastro")
async def cadastro(
    carreira_schema: CarreiraBase,
    usuario: dict = Depends(requer_admin), 
    session: Session = Depends(pegar_sessao) 
):
    """Cadastra uma nova carreira no sistema verificando duplicatas, disponível apenas para administradores"""
    carreira = session.query(Carreira).filter(Carreira.nome == carreira_schema.nome).first() 
    if carreira:
        raise HTTPException(status_code=400, detail="Carreira já cadastrada")
    nova_carreira = criar_carreira(session, carreira_schema)
    return {"message": f"Carreira cadastrada com sucesso: {nova_carreira.nome}"}


@carreiraRouter.put("/atualizar/{carreira_id}")
async def atualizar(
    carreira_id: int,
    carreira_schema: CarreiraBase,
    usuario: dict = Depends(requer_admin), 
    session: Session = Depends(pegar_sessao) 
):
    """Atualiza os dados de uma carreira existente pelo ID, disponível apenas para administradores"""
    carreira = atualizar_carreira(session, carreira_id, carreira_schema) 
    if not carreira:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    return {"message": f"Carreira atualizada com sucesso: {carreira.nome}"}


@carreiraRouter.delete("/deletar/{carreira_id}")
async def deletar(
    carreira_id: int,
    usuario: dict = Depends(requer_admin), 
    session: Session = Depends(pegar_sessao)
):
    """Remove uma carreira do sistema pelo ID, disponível apenas para administradores"""
    carreira = deletar_carreira(session, carreira_id)
    if not carreira:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    return {"message": f"Carreira deletada com sucesso: {carreira.nome}"}    
