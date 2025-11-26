from fastapi import APIRouter, HTTPException, Depends
from app.services.curso import criar_curso, listar_cursos, buscar_curso_por_id, atualizar_curso, deletar_curso
from app.schemas.cursoSchemas import CursoBase, CursoOut
from sqlalchemy.orm import Session
from app.dependencies import pegar_sessao, requer_admin
from app.models.cursoModels import Curso
from app.models.usuarioModels import Usuario


cursoRouter = APIRouter(prefix="/curso", tags=["curso"])


@cursoRouter.get("/", response_model=list[CursoOut])
async def get_cursos(session: Session = Depends(pegar_sessao)):
    """Lista todos os cursos cadastrados no sistema"""
    return listar_cursos(session)


@cursoRouter.get("/{curso_id}", response_model=CursoOut)
async def get_curso(curso_id: int, session: Session = Depends(pegar_sessao)):
    """Busca um curso específico pelo ID ou retorna erro 404 se não encontrado"""
    curso = buscar_curso_por_id(session, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return curso


@cursoRouter.post("/cadastro")
async def cadastro(
    curso_schema: CursoBase,
    usuario: dict = Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    """Cadastra um novo curso verificando duplicatas, disponível apenas para administradores"""
    curso = session.query(Curso).filter(Curso.nome == curso_schema.nome).first()
    if curso:
        raise HTTPException(status_code=400, detail="curso já cadastrado")
    novo_curso = criar_curso(session, curso_schema)
    return {"message": f"Curso cadastrado com sucesso: {novo_curso.nome}"}


@cursoRouter.put("/atualizar/{curso_id}")
async def atualizar(
    curso_id: int,
    curso_schema: CursoBase,
    usuario: dict = Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    """Atualiza os dados de um curso existente pelo ID, disponível apenas para administradores"""
    curso = atualizar_curso(session, curso_id, curso_schema)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return {"message": f"Curso atualizado com sucesso: {curso.nome}"}


@cursoRouter.delete("/deletar/{curso_id}")
async def deletar(
    curso_id: int,
    usuario: Usuario = Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    """Remove um curso do sistema pelo ID, disponível apenas para administradores"""
    curso = deletar_curso(session, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return {"message": f"Curso deletado com sucesso: {curso.nome}"}
