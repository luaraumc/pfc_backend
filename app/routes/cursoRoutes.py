from fastapi import APIRouter, HTTPException, Depends
from app.services.curso import criar_curso, listar_cursos, buscar_curso_por_id, atualizar_curso, deletar_curso
from app.services.cursoConhecimento import criar_curso_conhecimento, listar_curso_conhecimentos, remover_curso_conhecimento
from app.schemas.cursoSchemas import CursoBase, CursoOut
from app.schemas.cursoConhecimentoSchemas import CursoConhecimentoBase, CursoConhecimentoOut
from sqlalchemy.orm import Session
from app.dependencies import pegar_sessao, verificar_token, requer_admin
from app.models.cursoModels import Curso
from app.models.usuarioModels import Usuario
from app.models.cursoConhecimentoModels import CursoConhecimento

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

# ======================= CONHECIMENTOS DO CURSO =======================

@cursoRouter.get("/{curso_id}/conhecimentos", response_model=list[CursoConhecimentoOut])
async def listar_conhecimentos_curso_route(
    curso_id: int,
    session: Session = Depends(pegar_sessao)
):
    """Lista todos os conhecimentos associados a um curso específico"""
    return listar_curso_conhecimentos(session, curso_id)

@cursoRouter.post("/{curso_id}/adicionar-conhecimento/{conhecimento_id}", response_model=CursoConhecimentoOut)
async def adicionar_conhecimento_curso_route(
    curso_id: int,
    conhecimento_id: int,
    usuario: dict = Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    """Adiciona um conhecimento a um curso verificando duplicatas, disponível apenas para administradores"""
    existe = session.query(CursoConhecimento).filter_by(curso_id=curso_id, conhecimento_id=conhecimento_id).first()
    if existe:
        raise HTTPException(status_code=400, detail="Conhecimento já adicionado ao curso")
    curso_conhecimento_data = CursoConhecimentoBase(curso_id=curso_id, conhecimento_id=conhecimento_id)
    return criar_curso_conhecimento(session, curso_conhecimento_data)

@cursoRouter.delete("/{curso_id}/remover-conhecimento/{conhecimento_id}", response_model=CursoConhecimentoOut)
async def remover_conhecimento_curso_route(
    curso_id: int,
    conhecimento_id: int,
    usuario: dict = Depends(requer_admin),
    session: Session = Depends(pegar_sessao)
):
    """Remove a associação entre um curso e um conhecimento específico, disponível apenas para administradores"""
    resultado = remover_curso_conhecimento(session, curso_id, conhecimento_id)
    if not resultado:
        raise HTTPException(status_code=404, detail="Relação curso-conhecimento não encontrada")
    return resultado
