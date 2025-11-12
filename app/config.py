from dotenv import load_dotenv # carregar as variáveis de ambiente
from passlib.context import CryptContext # criptografia de senhas
from fastapi.security import OAuth2PasswordBearer # autenticação via OAuth2
import os # interagir com o sistema operacional

load_dotenv()

KEY_CRYPT = os.getenv('KEY_CRYPT') # chave de criptografia --> Irá pegar a senha do usuário e criptografar com essa chave fazendo com que a senha fique segura no banco de dados
ALGORITHM = os.getenv('ALGORITHM') # algoritmo de criptografia
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')) # tempo de expiração do token de acesso (em minutos)

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # define o esquema de criptografia --> (deprecated=auto) caso o esquema (bcrypt) fique obsoleto, ele irá atualizar automaticamente
oauth2_schema = OAuth2PasswordBearer(tokenUrl="auth/login") # define a url para o login (rota onde o usuário irá enviar suas credenciais para obter o token)
