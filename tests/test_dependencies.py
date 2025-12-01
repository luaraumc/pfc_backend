import importlib
import sys

import pytest
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _reload_dependencies(monkeypatch):
	"""Recarrega app.dependencies com envs e stub de create_engine, capturando a URL."""
	monkeypatch.setenv("KEY_CRYPT", "k")
	monkeypatch.setenv("ALGORITHM", "HS256")
	monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
	monkeypatch.setenv("DB_USER", "u")
	monkeypatch.setenv("DB_PASSWORD", "p")
	monkeypatch.setenv("DB_HOST", "h")
	monkeypatch.setenv("DB_PORT", "5432")
	monkeypatch.setenv("DB_NAME", "db")

	captured = {"url": None}

	class DummyEngine:
		__test__ = False
		def __init__(self, url):
			self.url = url

	def fake_create_engine(url):
		captured["url"] = url
		return DummyEngine(url)

	monkeypatch.setattr(sqlalchemy, "create_engine", fake_create_engine)

	sys.modules.pop("app.dependencies", None)
	deps = importlib.import_module("app.dependencies")
	return deps, captured


def _make_sqlite_session_and_models(deps):
	"""Cria sessão SQLite em memória e inicializa Base para testes isolados."""
	sys.modules.pop("app.models", None)
	from app.models import Base

	engine = create_engine("sqlite+pysqlite:///:memory:")
	TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	Base.metadata.create_all(bind=engine)
	return TestingSessionLocal(), Base, engine


def test_builds_database_url_and_engine_stub(monkeypatch):
	"""Verifica montagem da DATABASE_URL e uso do engine stub."""
	deps, captured = _reload_dependencies(monkeypatch)
	expected_url = "postgresql+psycopg2://u:p@h:5432/db"
	assert deps.DATABASE_URL == expected_url
	assert captured["url"] == expected_url
	assert getattr(deps.engine, "url", None) == expected_url


def test_pegar_sessao_yields_sqlite_session(monkeypatch):
	"""Garante que pegar_sessao fornece e fecha uma sessão SQLite válida."""
	deps, _ = _reload_dependencies(monkeypatch)
	session, Base, engine = _make_sqlite_session_and_models(deps)
	deps.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

	gen = deps.pegar_sessao()
	db = next(gen)
	from sqlalchemy.orm import Session as SASession

	assert isinstance(db, SASession)

	try:
		next(gen)
	except StopIteration:
		pass


def test_verificar_token_success(monkeypatch):
	"""Valida que verificar_token retorna o usuário quando o JWT contém sub válido."""
	deps, _ = _reload_dependencies(monkeypatch)
	db, Base, engine = _make_sqlite_session_and_models(deps)

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

	def fake_decode(token, key, alg):
		return {"sub": str(user.id)}

	monkeypatch.setattr(deps.jwt, "decode", fake_decode)

	out = deps.verificar_token(token="abc", session=db)
	assert out.id == user.id
	assert out.email == "u@e.com"


def test_verificar_token_usuario_nao_encontrado(monkeypatch):
	"""Garante 401 quando sub do token não corresponde a usuário existente."""
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
	"""Garante 401 quando jwt.decode lança erro indicando token inválido."""
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
	"""Permite admin=True e lança 403 quando admin=False."""
	deps, _ = _reload_dependencies(monkeypatch)
	assert deps.requer_admin(usuario={"admin": True}) == {"admin": True}
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

