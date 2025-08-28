# executar no terminal para rodar: python -m uvicorn app.main:app --reload
from fastapi import FastAPI

app = FastAPI()

from app.routes.loginRoutes import loginRouter
from app.routes.homeRoutes import homeRouter
from app.routes.cadastroRoutes import cadastroRouter

app.include_router(loginRouter)
app.include_router(homeRouter)
app.include_router(cadastroRouter)
