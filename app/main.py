# executar no terminal para rodar: python -m uvicorn app.main:app --reload

from fastapi import FastAPI # classe FastAPI

app = FastAPI() # instancia da classe FastAPI

# importando as rotas
from app.routes.authRoutes import authRouter
from app.routes.usuarioRoutes import usuarioRouter
from app.routes.carreiraRoutes import carreiraRouter
from app.routes.cursoRoutes import cursoRouter

# incluindo as rotas na aplicação FastAPI instanciada
app.include_router(authRouter)
app.include_router(usuarioRouter)
app.include_router(carreiraRouter)
app.include_router(cursoRouter)
