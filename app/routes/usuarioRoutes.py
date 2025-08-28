from fastapi import APIRouter
from services.usuario import criar_usuario, atualizar_usuario, listar_usuarios, buscar_usuario_por_id

usuarioRouter = APIRouter(prefix="/auth", tags=["auth"])

@usuarioRouter.post("/login")
async def login():
    return {"message": "Login"}

@usuarioRouter.post("/cadastro")
async def cadastro():
    return {"message": "Cadastro"}
