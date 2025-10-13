# executar no terminal para rodar: python -m uvicorn app.main:app --reload

from fastapi import FastAPI # classe FastAPI
from fastapi.middleware.cors import CORSMiddleware # middleware para permitir requisições de diferentes origens

app = FastAPI() # instancia da classe FastAPI

# definindo as origens permitidas para requisições CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]


# configurando o middleware CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,

    allow_methods=["*"],
    allow_headers=["*"],
)

# importando as rotas
from app.routes.authRoutes import authRouter
from app.routes.usuarioRoutes import usuarioRouter
from app.routes.carreiraRoutes import carreiraRouter
from app.routes.cursoRoutes import cursoRouter
from app.routes.habilidadeRoutes import habilidadeRouter
from app.routes.conhecimentoRoutes import conhecimentoRouter
from app.routes.vagaRoutes import vagaRouter

# incluindo as rotas na aplicação FastAPI instanciada
app.include_router(authRouter)
app.include_router(usuarioRouter)
app.include_router(carreiraRouter)
app.include_router(cursoRouter)
app.include_router(habilidadeRouter)
app.include_router(conhecimentoRouter)
app.include_router(vagaRouter)
