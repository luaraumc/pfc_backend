from fastapi import APIRouter, Depends, HTTPException
from app.services.usuario import criar_usuario, atualizar_usuario, listar_usuarios, buscar_usuario_por_id
from sqlalchemy.orm import sessionmaker, Session
from app.models import Usuario
from app.dependencies import pegar_sessao, setup_database
from app.main import bcrypt_context
from app.schemas import UsuarioBase

usuarioRouter = APIRouter(prefix="/auth", tags=["auth"])

@usuarioRouter.post("/login")
async def login():
    return {"message": "Login"}

@usuarioRouter.post("/cadastro")
async def cadastro(usuario_schema: UsuarioBase, session: Session = Depends(pegar_sessao)): # passa como parametro os dados que o usuário vai inserir ao acessar a rota e a sessão do banco de dados
    usuario = session.query(Usuario).filter(Usuario.email == usuario_schema.email).first() # verifica se o email já existe no banco de dados. (first pega o primeiro resultado que encontrar, se encontrar algum resultado, significa que o email já existe)
    if usuario: 
        # se ja existir um usuario com esse email, retorna um erro
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    else:
        # se não existir, cria o usuário
        senha_criptografada = bcrypt_context.hash(usuario_schema.senha) # criptografa a senha do usuário
        criar_usuario(session, usuario_schema.nome, usuario_schema.email, senha_criptografada, usuario_schema.carreira_id, usuario_schema.curso_id)
        return {"message": f"Usuário cadastrado com sucesso {usuario_schema.email}"}
    
@usuarioRouter.get("/carreiras")
async def listar_carreiras(session: Session = Depends(pegar_sessao)):
    carreiras = session.execute("SELECT * FROM carreiras").fetchall()
    return listar_usuarios(session)
