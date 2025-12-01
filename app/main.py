from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# python -m uvicorn app.main:app --reload

app = FastAPI()

# configurando o middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routes.authRoutes import authRouter
from app.routes.carreiraHabilidadeRoutes import carreiraHabilidadeRouter
from app.routes.carreiraRoutes import carreiraRouter
from app.routes.conhecimentoCategoriaRoutes import conhecimentoCategoriaRouter
from app.routes.conhecimentoRoutes import conhecimentoRouter
from app.routes.cursoConhecimentoRoutes import cursoConhecimentoRouter
from app.routes.cursoRoutes import cursoRouter
from app.routes.habilidadeRoutes import habilidadeRouter
from app.routes.mapeamentoRoutes import mapeamentoRouter
from app.routes.usuarioHabilidadeRoutes import usuarioHabilidadeRouter
from app.routes.usuarioRoutes import usuarioRouter
from app.routes.vagaRoutes import vagaRouter

app.include_router(authRouter)
app.include_router(carreiraHabilidadeRouter)
app.include_router(carreiraRouter)
app.include_router(conhecimentoCategoriaRouter)
app.include_router(conhecimentoRouter)
app.include_router(cursoConhecimentoRouter)
app.include_router(cursoRouter)
app.include_router(habilidadeRouter)
app.include_router(mapeamentoRouter)
app.include_router(usuarioHabilidadeRouter)
app.include_router(usuarioRouter)
app.include_router(vagaRouter)
