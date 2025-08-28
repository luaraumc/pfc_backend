from fastapi import APIRouter, HTTPException


cadastroRouter = APIRouter(prefix="/cadastro", tags=["cadastro"])

@cadastroRouter.get("/")
async def criar_usuario():
    # funcionalidade para criar um novo usuário (inserir campos como nome, email, senha, curso, carreira desejada, habilidades possuidas)
    # após confirmar o cadastro o usuário deve ser redirecionado para a rota/tela de login

    return {"message": "Usuário criado com sucesso"}

async def verificar_usuario():
    # funcionalidade para verificar se um usuário já existe, se não existir, criar um novo usuário
    return {"message": "Verificação de usuário"}





