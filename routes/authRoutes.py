from fastapi import APIRouter
from services.usuarios import listar_usuarios, buscar_usuario_por_id

authRouter = APIRouter(prefix="/auth", tags=["auth"])

@authRouter.post("/login")
async def login():
    return {"message": "Login"}

@authRouter.post("/register")
async def register():
    return {"message": "Register"}
