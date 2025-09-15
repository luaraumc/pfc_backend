from fastapi import APIRouter, HTTPException, Depends # cria dependências e exceções HTTP
from app.services.curso import criar_curso, listar_cursos, buscar_curso_por_id, atualizar_curso, deletar_curso # serviços relacionados ao curso
from app.schemas import CursoBase, CursoOut # schemas para validação de dados
from sqlalchemy.orm import Session # pegar a sessão do banco de dados
from app.dependencies import pegar_sessao, verificar_token # cria sessões com o banco de dados e verifica o token
from app.models import Curso # modelo de tabela definido no arquivo models.py

# Inicializa o router
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

# Cadastrar curso - AUTENTICADA
@cursoRouter.post("/cadastro")
async def cadastro(
    curso_schema: CursoBase, # passa como parametro os dados que o usuário tem que inserir ao acessar a rota
    usuario: dict = Depends(verificar_token), # verifica o token de acesso do usuário
    session: Session = Depends(pegar_sessao) # pega a sessão do banco de dados
):
    curso = session.query(Curso).filter(Curso.nome == curso_schema.nome).first() # verifica se o curso já existe no banco de dados
    if curso:
        raise HTTPException(status_code=400, detail="curso já cadastrado")
    novo_curso = criar_curso(session, curso_schema) # se não existir, cria o curso
    return {"message": f"Curso cadastrado com sucesso: {novo_curso.nome}"}

# Atualizar curso - AUTENTICADA
@cursoRouter.put("/atualizar/{curso_id}")
async def atualizar(
    curso_id: int, # ID do curso a ser atualizado
    curso_schema: CursoBase, # passa como parametro os dados que o usuário tem que inserir ao acessar a rota
    usuario: dict = Depends(verificar_token), # verifica o token de acesso do usuário
    session: Session = Depends(pegar_sessao) # pega a sessão do banco de dados
):
    curso = atualizar_curso(session, curso_id, curso_schema) # chama a função de serviço para atualizar o curso
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return {"message": f"Curso atualizado com sucesso: {curso.nome}"}

# Deletar curso - AUTENTICADA
@cursoRouter.delete("/deletar/{curso_id}")
async def deletar(
    curso_id: int, # ID do curso a ser deletado
    usuario: dict = Depends(verificar_token), # verifica o token de acesso do usuário
    session: Session = Depends(pegar_sessao) # pega a sessão do banco de dados
):
    curso = deletar_curso(session, curso_id) # chama a função de serviço para deletar o curso
    if not curso:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return {"message": f"Curso deletado com sucesso: {curso.nome}"}
