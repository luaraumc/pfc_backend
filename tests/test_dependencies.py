

"""
Testes do módulo app.dependencies

Este arquivo valida comportamentos principais das dependências da aplicação:

- test_builds_database_url_and_engine_stub:
	Garante que a DATABASE_URL seja montada a partir das variáveis de ambiente
	(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME) e que sqlalchemy.create_engine
	(stubado) seja chamado com essa URL. O engine dummy expõe o atributo `url`.

- test_pegar_sessao_yields_sqlite_session:
	Verifica que o generator `pegar_sessao` fornece uma sessão SQLAlchemy funcional
	e a finaliza corretamente (fechando a sessão) quando o generator termina.

- test_verificar_token_success:
	Simula `jwt.decode` retornando um `sub` válido e confirma que `verificar_token`
	busca e retorna o usuário correto do banco.

- test_verificar_token_usuario_nao_encontrado:
	Quando o `sub` decodificado não corresponde a um usuário existente, espera-se
	`HTTPException` 401 com detalhe "Acesso inválido".

- test_verificar_token_invalido_raise_401:
	Quando `jwt.decode` lança `JWTError`, `verificar_token` deve levantar
	`HTTPException` 401 com detalhe "Acesso negado, verifique a validade do token".

- test_requer_admin:
	Aceita quando `usuario` indica `admin=True` e lança `HTTPException` 403
	("Acesso restrito") quando `admin=False`.

Utilitários internos deste arquivo:
- _reload_dependencies(monkeypatch): Configura variáveis de ambiente necessárias,
	substitui `sqlalchemy.create_engine` por um stub e reimporta `app.dependencies`.
- _make_sqlite_session_and_models(deps): Cria um engine SQLite em memória, prepara
	`Session` e modelos (via `Base`) para testes isolados.
"""

import importlib
import sys

import pytest
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _reload_dependencies(monkeypatch):
	# Vars para app.config e DB URL
	monkeypatch.setenv("KEY_CRYPT", "k")
	monkeypatch.setenv("ALGORITHM", "HS256")
	monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
	monkeypatch.setenv("DB_USER", "u")
	monkeypatch.setenv("DB_PASSWORD", "p")
	monkeypatch.setenv("DB_HOST", "h")
	monkeypatch.setenv("DB_PORT", "5432")
	monkeypatch.setenv("DB_NAME", "db")

	# Stub de create_engine para evitar import de psycopg2
	captured = {"url": None}

	class DummyEngine:
		__test__ = False  # evitar que pytest o trate como teste
		def __init__(self, url):
			self.url = url

	def fake_create_engine(url):
		captured["url"] = url
		return DummyEngine(url)

	monkeypatch.setattr(sqlalchemy, "create_engine", fake_create_engine)

	# Reimportar módulo
	sys.modules.pop("app.dependencies", None)
	deps = importlib.import_module("app.dependencies")
	return deps, captured


def _make_sqlite_session_and_models(deps):
	# Garantir modelos usando o Base reimportado
	sys.modules.pop("app.models", None)
	from app.models import Base  # noqa: E402

	engine = create_engine("sqlite+pysqlite:///:memory:")
	TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	Base.metadata.create_all(bind=engine)
	return TestingSessionLocal(), Base, engine


def test_builds_database_url_and_engine_stub(monkeypatch):
	deps, captured = _reload_dependencies(monkeypatch)
	expected_url = "postgresql+psycopg2://u:p@h:5432/db"
	assert deps.DATABASE_URL == expected_url
	assert captured["url"] == expected_url
	# engine é o dummy com atributo url
	assert getattr(deps.engine, "url", None) == expected_url


def test_pegar_sessao_yields_sqlite_session(monkeypatch):
	deps, _ = _reload_dependencies(monkeypatch)
	session, Base, engine = _make_sqlite_session_and_models(deps)
	# Patchar SessionLocal para usar o SQLite em memória
	deps.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

	# Usar generator pegar_sessao para obter uma sessão funcional
	gen = deps.pegar_sessao()
	db = next(gen)
	# Criar e consultar algo simples: inserir zero tabelas aqui só para checar type
	from sqlalchemy.orm import Session as SASession

	assert isinstance(db, SASession)

	# Finaliza generator (fecha sessão)
	try:
		next(gen)
	except StopIteration:
		pass


def test_verificar_token_success(monkeypatch):
	deps, _ = _reload_dependencies(monkeypatch)
	db, Base, engine = _make_sqlite_session_and_models(deps)

	# Preparar usuário
	from app.models import Usuario, Carreira, Curso

	car = Carreira(nome="N", descricao="D")
	cur = Curso(nome="C", descricao="DD")
	db.add_all([car, cur])
	db.commit()
	db.refresh(car)
	db.refresh(cur)
	user = Usuario(nome="U", email="u@e.com", senha="S3nh@!", admin=False, carreira_id=car.id, curso_id=cur.id)
	db.add(user)
	db.commit()
	db.refresh(user)

	# Monkeypatch do jwt.decode para retornar sub
	def fake_decode(token, key, alg):
		return {"sub": str(user.id)}

	monkeypatch.setattr(deps.jwt, "decode", fake_decode)

	out = deps.verificar_token(token="abc", session=db)
	assert out.id == user.id
	assert out.email == "u@e.com"


def test_verificar_token_usuario_nao_encontrado(monkeypatch):
	deps, _ = _reload_dependencies(monkeypatch)
	db, Base, engine = _make_sqlite_session_and_models(deps)

	def fake_decode(token, key, alg):
		return {"sub": "999999"}

	monkeypatch.setattr(deps.jwt, "decode", fake_decode)

	with pytest.raises(Exception) as ctx:
		deps.verificar_token(token="abc", session=db)
	ex = ctx.value
	from fastapi import HTTPException

	assert isinstance(ex, HTTPException)
	assert ex.status_code == 401
	assert ex.detail == "Acesso inválido"


def test_verificar_token_invalido_raise_401(monkeypatch):
	deps, _ = _reload_dependencies(monkeypatch)
	db, Base, engine = _make_sqlite_session_and_models(deps)

	def fake_decode(token, key, alg):
		raise deps.JWTError("bad")

	monkeypatch.setattr(deps.jwt, "decode", fake_decode)

	from fastapi import HTTPException

	with pytest.raises(HTTPException) as ctx:
		deps.verificar_token(token="x", session=db)
	ex = ctx.value
	assert ex.status_code == 401
	assert ex.detail == "Acesso negado, verifique a validade do token"


def test_requer_admin(monkeypatch):
	deps, _ = _reload_dependencies(monkeypatch)

	# dict com admin True passa
	assert deps.requer_admin(usuario={"admin": True}) == {"admin": True}

	# objeto com admin False falha
	class UserObj:
		def __init__(self):
			self.admin = False

	with pytest.raises(Exception) as ctx:
		deps.requer_admin(usuario=UserObj())
	from fastapi import HTTPException

	ex = ctx.value
	assert isinstance(ex, HTTPException)
	assert ex.status_code == 403
	assert ex.detail == "Acesso restrito"

