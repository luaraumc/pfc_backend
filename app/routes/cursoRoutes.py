from fastapi import APIRouter, HTTPException, Depends
from app.services.curso import criar_curso, listar_cursos, buscar_curso_por_id, atualizar_curso, deletar_curso
from app.schemas import CursoBase, CursoOut
from sqlalchemy.orm import Session
from app.dependencies import pegar_sessao
from app.models import Curso

cursoRouter = APIRouter(prefix="/curso", tags=["curso"])

# Listar todos os cursos
@cursoRouter.get("/", response_model=list[CursoOut]) # response_model: validar e filtrar os dados antes de enviar ao cliente
async def get_cursos(session: Session = Depends(pegar_sessao)):
    return listar_cursos(session)
 
# Buscar curso por ID
@cursoRouter.get("/{curso_id}", response_model=CursoOut) # response_model: validar e filtrar os dados antes de enviar ao cliente
async def get_curso(curso_id: int, session: Session = Depends(pegar_sessao)):
    curso = buscar_curso_por_id(session, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return curso

# Cadastrar curso
@cursoRouter.post("/cadastro")
async def cadastro(curso_schema: CursoBase, session: Session = Depends(pegar_sessao)): # passa como parametro os dados que o usuário tem que inserir ao acessar a rota e a sessão do banco de dados
    curso = session.query(Curso).filter(Curso.nome == curso_schema.nome).first() # verifica se o curso já existe no banco de dados. (first pega o primeiro resultado que encontrar, se encontrar algum resultado, significa que a curso já existe)
    if curso: 
        raise HTTPException(status_code=400, detail="curso já cadastrado") # se ja existir um curso com esse nome, retorna um erro
    else:
        novo_curso = criar_curso(session, curso_schema)
        return {"message": f"Curso cadastrado com sucesso: {novo_curso.nome}"}

# Atualizar curso
@cursoRouter.put("/atualizar/{curso_id}")
async def atualizar(curso_id: int, curso_schema: CursoBase, session: Session = Depends(pegar_sessao)):
    curso = atualizar_curso(session, curso_id, curso_schema)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return {"message": f"Curso atualizado com sucesso: {curso.nome}"}

# Deletar curso
@cursoRouter.delete("/deletar/{curso_id}")
async def deletar(curso_id: int, session: Session = Depends(pegar_sessao)):
    curso = deletar_curso(session, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return {"message": f"Curso deletado com sucesso: {curso.nome}"}