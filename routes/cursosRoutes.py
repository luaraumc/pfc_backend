from fastapi import FastAPI, HTTPException # HTTPException: retornar erros HTTP personalizados
from cursos import listar_cursos, buscar_curso_por_id

app = FastAPI()

@app.get("/cursos")
def get_cursos():
    return listar_cursos()

@app.get("/cursos/{curso_id}")
def get_curso(curso_id: int):
    curso = buscar_curso_por_id(curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return curso

