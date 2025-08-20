from fastapi import APIRouter, HTTPException
from carreiras import listar_carreiras, buscar_carreira_por_id

carreirasRouter = APIRouter(prefix="/carreiras", tags=["carreiras"])

@carreirasRouter.get("/")
def get_carreiras():
    return listar_carreiras()

@carreirasRouter.get("/{carreira_id}")
def get_carreira(carreira_id: int):
    carreira = buscar_carreira_por_id(carreira_id)
    if not carreira:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    return carreira
