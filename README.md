# Backend

API REST construída com FastAPI, SQLAlchemy e Alembic. Inclui autenticação via JWT, gestão de usuários, carreiras, cursos, habilidades, vagas e extração de habilidades com suporte OpenAI.

## Configuração do ambiente

1) Crie e ative um ambiente virtual

```
python -m venv .venv
.venv\Scripts\activate
```

2) Instale as dependências

```
pip install -r requirements.txt
```

3) Crie um arquivo `.env` na pasta `pfc_backend/` com as variáveis abaixo:

```
# Banco de dados
DB_HOST=host
DB_PORT=port
DB_NAME=banco
DB_USER=usuario
DB_PASSWORD=senha

# Autenticação/JWT
KEY_CRYPT=chave_secreta_aleatoria
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Resend
RESEND_API_KEY=chave_resend
EMAIL_FROM=email@dominio.com>

# OpenAI
OPENAI_API_KEY=chave_openai

```

4) Configure o Alembic

O arquivo `alembic.ini` contém a chave `sqlalchemy.url`. Garanta que ela aponte para o mesmo banco especificado no `.env`.

## Rodando o servidor

Com o ambiente virtual ativo e dependências instaladas:

```
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Docs interativas (Swagger UI): http://127.0.0.1:8000/docs

## Migrações de banco (Alembic)

Execute as migrações para criar/atualizar o schema do banco:

```
alembic upgrade head
```

Para criar uma nova revisão (após alterações em modelos):

```
alembic revision -m "sua_mensagem" --autogenerate
alembic upgrade head
```

Observação: O projeto já possui diversas revisões em `alembic/versions/`, incluindo seeds de normalização/categorias/habilidades. Ao rodar `upgrade head`, esses seeds serão aplicados conforme definido nas revisões.

## Estrutura do projeto

```
pfc_backend/
	app/
		main.py                # instancia FastAPI, CORS e inclui as rotas
		config.py              # JWT (algoritmo, chave, expiração) e OAuth2 schema
		dependencies.py        # engine, SessionLocal, Base e dependências (auth/admin)
		models.py              # modelos SQLAlchemy (tabelas e relacionamentos)
		schemas.py             # Pydantic schemas de entrada/saída
		routes/                # rotas agrupadas (auth, usuario, carreira, curso, etc.)
		services/              # regras de negócio (CRUDs e extras)
		utils/errors.py        # utilitários de erro/validação
	alembic/                 # migrações de banco
	requirements.txt         # dependências Python
	Procfile                 # comando para deploy (uvicorn)
```

## Deploy

O `Procfile` contém o comando de inicialização para plataformas compatíveis (ex.: Railway):

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"
```

## Dicas e problemas comuns

- Erro de CORS: ajuste os domínios permitidos em `app/main.py`.
- Erro de conexão ao banco: verifique `.env` e o `alembic.ini`.
- Seeds não aplicados: confirme que `alembic upgrade head` rodou sem erros e que a `sqlalchemy.url` está correta.

## Licença

Este projeto é de uso interno.
