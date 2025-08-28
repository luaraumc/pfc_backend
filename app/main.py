# executar no terminal para rodar: python -m uvicorn main:app --reload

from fastapi import FastAPI

app = FastAPI()

from routes.authRoutes import authRouter
from pfc_backend.app.routes.carreiraRoutes import carreirasRouter
from pfc_backend.app.routes.cursoRoutes import cursosRouter

app.include_router(authRouter)
app.include_router(carreirasRouter)
app.include_router(cursosRouter)

