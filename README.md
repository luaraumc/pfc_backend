# Rumo Techno Backend

Backend que transforma descrições de vagas de emprego de TI em skills padronizadas (com suporte OpenAI) e fornece endpoints para gestão de usuários, verificação de compatibilidade entre perfis e carreiras em tempo real e envio de notificações por e-mail.

Principais recursos:
- Autenticação via JWT
- Gestão de perfis de usuários
- Modelagem de carreiras, habilidades, cursos, conhecimentos e vagas
- Extração/normalização automática de habilidades técnicas (OpenAI)
- Envio de e-mails transacionais (Resend)
- Migrações com Alembic e integração com PostgreSQL

---

## Sumário
- [Tecnologias](#tecnologias)
- [Instalação](#instalação)
- [Configuração (variáveis de ambiente)](#configuração-variáveis-de-ambiente)
- [Banco de dados e migrações (Alembic)](#banco-de-dados-e-migrações-alembic)
- [Executando o servidor](#executando-o-servidor)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Deploy](#deploy)
- [Dicas e problemas comuns](#dicas-e-problemas-comuns)
- [Licença](#licença)

---

## Tecnologias
- Python (FastAPI, Pydantic)
- SQLAlchemy (ORM) e Alembic (migrações)
- JWT (autenticação)
- Resend (e-mail)
- OpenAI

---

## Instalação

1) Crie e ative um ambiente virtual

No Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```


2) Instale as dependências
```bash
pip install -r requirements.txt
```

---

## Configuração (variáveis de ambiente)

Crie um arquivo `.env` na pasta `pfc_backend/` com as variáveis abaixo:

```env
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
EMAIL_FROM=email@dominio.com

# OpenAI
OPENAI_API_KEY=chave_openai
```

Configure o Alembic

No arquivo `alembic.ini`, garanta que a chave `sqlalchemy.url` aponte para o mesmo banco especificado no `.env`.

---

## Banco de dados e migrações (Alembic)

Aplicar as migrações para criar/atualizar o schema:
```bash
alembic upgrade head
```

Observação: O projeto já possui diversas revisões em `alembic/versions/`, incluindo seeds de normalização/categorias/habilidades. Ao rodar `upgrade head`, esses seeds serão aplicados conforme necessário.

---

## Executando o servidor

Com o ambiente virtual ativo e dependências instaladas:
```bash
python -m uvicorn app.main:app --reload
```

Ajuste CORS em `app/main.py` e outras configs em `app/config.py`.

---

## Estrutura do projeto

```
pfc_backend/
  app/
    main.py                # instancia FastAPI, CORS e inclui as rotas
    config.py              # JWT (algoritmo, chave, expiração) e OAuth2 schema
    dependencies.py        # engine, SessionLocal, Base e dependências (auth/admin)
    models/                # modelos SQLAlchemy (tabelas e relacionamentos)
    schemas/               # Pydantic schemas de entrada/saída
    routes/                # rotas agrupadas (auth, usuario, carreira, curso, etc.)
    services/              # regras de negócio (CRUDs e extras)
    utils/
      errors.py            # utilitários de erro/validação
  alembic/                 # migrações de banco
  requirements.txt         # dependências Python
  Procfile                 # comando para deploy (uvicorn)
```

---

## Deploy

O `Procfile` contém o comando de inicialização para plataformas compatíveis (ex.: Railway):
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"
```

Garanta que as variáveis de ambiente de produção estejam configuradas na plataforma de deploy.

---

## Dicas e problemas comuns
- Erro de CORS: ajuste os domínios permitidos em `app/main.py`.
- Erro de conexão ao banco: verifique o `.env` e o `alembic.ini` (especialmente `sqlalchemy.url`).
- Seeds não aplicados: confirme que `alembic upgrade head` rodou sem erros e que a `sqlalchemy.url` está correta.

---

## Licença

Este projeto é de uso interno.
