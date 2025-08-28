from fastapi import APIRouter
from pfc_backend.app.services.usuario import criar_usuario, atualizar_usuario, listar_usuarios, buscar_usuario_por_id

authRouter = APIRouter(prefix="/auth", tags=["auth"])

@authRouter.post("/login")
async def login():
    return {"message": "Login"}

@authRouter.post("/cadastro")
async def cadastro():
    return {"message": "Cadastro"}
