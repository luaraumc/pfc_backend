from dotenv import load_dotenv
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
import os 

load_dotenv()

KEY_CRYPT = os.getenv('KEY_CRYPT') # chave de criptografia
ALGORITHM = os.getenv('ALGORITHM') # algoritmo de criptografia
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')) # tempo de expiração do token de acesso

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # define o esquema de criptografia --> (deprecated=auto) caso o esquema (bcrypt) fique obsoleto, ele irá atualizar automaticamente
oauth2_schema = OAuth2PasswordBearer(tokenUrl="auth/login") # define a rota onde o usuário irá enviar suas credenciais para obter o token
