from fastapi import FastAPI, HTTPException
from carreira import listar_carreiras, buscar_carreira_por_id

app = FastAPI()

@app.get("/carreira")
def get_carreiras():
    return listar_carreiras()

@app.get("/carreira/{carreira_id}")
def get_carreira(carreira_id: int):
    carreira = buscar_carreira_por_id(carreira_id)
    if not carreira:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    return carreira
