# executar no terminal para rodar: python -m uvicorn app.main:app --reload
from fastapi import FastAPI
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

kEY_CRYPT = os.getenv('KEY_CRYPT') # chave de criptografia --> Irá pegar a senha do usuário e criptografar com essa chave fazendo com que a senha fique segura no banco de dados
ALGORITHM = os.getenv('ALGORITHM') # algoritmo de criptografia
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES'))# tempo de expiração do token de acesso (em minutos)

app = FastAPI()

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # define o esquema de criptografia --> (deprecated=auto) caso o esquema (bcrypt) fique obsoleto, ele irá atualizar automaticamente


from app.routes.usuarioRoutes import usuarioRouter
from app.routes.carreiraRoutes import carreiraRouter
from app.routes.cursoRoutes import cursoRouter

app.include_router(usuarioRouter)
app.include_router(carreiraRouter)
app.include_router(cursoRouter)
