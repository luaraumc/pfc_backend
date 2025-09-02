from fastapi import APIRouter, HTTPException, Depends
from app.services.curso import listar_cursos, buscar_curso_por_id
from app.schemas import CursoBase
from sqlalchemy.orm import Session
from app.dependencies import pegar_sessao
from app.models import Curso
from app.services.curso import criar_curso

cursoRouter = APIRouter(prefix="/curso", tags=["curso"])

@cursoRouter.get("/")
def get_cursos():
    return listar_cursos()


@cursoRouter.post("/cadastro_curso")
async def cadastro(curso_schema: CursoBase, session: Session = Depends(pegar_sessao)): # passa como parametro os dados que o usuário vai inserir ao acessar a rota e a sessão do banco de dados
    curso = session.query(Curso).filter(Curso.nome == curso_schema.nome).first() # verifica se o curso já existe no banco de dados. (first pega o primeiro resultado que encontrar, se encontrar algum resultado, significa que a curso já existe)
    if curso: 
        # se ja existir um usuario com esse email, retorna um erro
        raise HTTPException(status_code=400, detail="curso já cadastrado")
    else:
       
        novo_curso = criar_curso(session, curso_schema)
        return {"message": f"curso cadastrado com sucesso: {novo_curso.nome}"}
    

@cursoRouter.get("/{curso_id}")
def get_curso(curso_id: int):
    curso = buscar_curso_por_id(curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return curso

