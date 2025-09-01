# executar no terminal para rodar: python -m uvicorn app.main:app --reload

from fastapi import FastAPI
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

kEY_CRYPT = os.getenv('KEY_CRYPT') # chave de criptografia --> Irá pegar a senha do usuário e criptografar com essa chave fazendo com que a senha fique segura no banco de dados


app = FastAPI()

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # define o esquema de criptografia --> (deprecated=auto) caso o esquema (bcrypt) fique obsoleto, ele irá atualizar automaticamente


from app.routes.usuarioRoutes import usuarioRouter
from app.routes.carreiraRoutes import carreirasRouter
from app.routes.cursoRoutes import cursosRouter

app.include_router(usuarioRouter)
app.include_router(carreirasRouter)
app.include_router(cursosRouter)

