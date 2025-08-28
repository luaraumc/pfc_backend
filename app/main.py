# executar no terminal para rodar: python -m uvicorn main:app --reload

from fastapi import FastAPI

app = FastAPI()

from routes.usuarioRoutes import usuarioRouter
from routes.carreiraRoutes import carreirasRouter
from routes.cursoRoutes import cursosRouter

app.include_router(usuarioRouter)
app.include_router(carreirasRouter)
app.include_router(cursosRouter)

