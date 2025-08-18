from fastapi import FastAPI, HTTPException # HTTPException: retornar erros HTTP personalizados
from carreiras import listar_carreiras, buscar_carreira_por_id

app = FastAPI()

@app.get("/carreiras")
def get_carreiras():
    return listar_carreiras()

@app.get("/carreiras/{carreira_id}")
def get_carreira(carreira_id: int):
    carreira = buscar_carreira_por_id(carreira_id)
    if not carreira:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    return carreira
