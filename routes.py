from fastapi import FastAPI, HTTPException
from cursos import criar_curso, listar_cursos, buscar_curso_por_id, atualizar_curso, deletar_curso, Curso

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


@app.post("/cursos")
def post_curso(curso: Curso):
    curso_id = criar_curso(curso.id, curso.nome, curso.descricao, curso.criado_em, curso.atualizado_em)
    return {"id": curso_id}

@app.put("/cursos/{curso_id}")
def put_curso(curso_id: int, curso: Curso):
    atualizar_curso(curso_id, curso.nome, curso.descricao, curso.atualizado_em)
    return {"status": "atualizado"}

@app.delete("/cursos/{curso_id}")
def delete_curso(curso_id: int):
    deletar_curso(curso_id)
    return {"status": "deletado"}
