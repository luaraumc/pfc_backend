from fastapi import APIRouter

loginRouter = APIRouter(prefix="/login", tags=["login"])


@loginRouter.post("/")
async def login():
    # verifica as credencias no banco de dados
    # se as credenciais forem válidas, retorna um token de acesso
    # caso contrário, retorna um erro de autenticação
    return {"message": "Login"}

@loginRouter.post('/esqueci-senha')
async def forgot_password():
    # verificar se o email está cadastrado no sistema
    # funcionalidade para enviar um email de recuperação de senha (se o email estiver cadastrado no sistema)
    return {"message": "Forgot Password"}