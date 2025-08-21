from fastapi import APIRouter, HTTPException
from services.cursos import listar_cursos, buscar_curso_por_id

cursosRouter = APIRouter(prefix="/cursos", tags=["cursos"])

@cursosRouter.get("/")
def get_cursos():
    return listar_cursos()

@cursosRouter.get("/{curso_id}")
def get_curso(curso_id: int):
    curso = buscar_curso_por_id(curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return curso

