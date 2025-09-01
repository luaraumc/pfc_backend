from fastapi import APIRouter, Depends
from app.services.usuario import criar_usuario, atualizar_usuario, listar_usuarios, buscar_usuario_por_id
from sqlalchemy.orm import sessionmaker
from app.models import Usuario
from app.dependencies import pegar_sessao, setup_database
from app.main import bcrypt_context


usuarioRouter = APIRouter(prefix="/auth", tags=["auth"])

@usuarioRouter.post("/login")
async def login():
    return {"message": "Login"}

@usuarioRouter.post("/cadastro")
async def cadastro(nome, email, senha, carreira_id, curso_id, session = Depends(pegar_sessao)): # passa como parametro os dados que o usuário vai inserir ao acessar a rota e a sessão do banco de dados
    usuario = session.query(Usuario).filter(Usuario.email == email).first() # verifica se o email já existe no banco de dados. (first pega o primeiro resultado que encontrar, se encontrar algum resultado, significa que o email já existe)
    if usuario:
        return {"error": "Usuário já existe"}
    else:
        senha_criptografada = bcrypt_context.hash(senha) # criptografa a senha do usuário
        criar_usuario(session, nome, email, senha_criptografada)
        return {"message": "Usuário cadastrado com sucesso"}
