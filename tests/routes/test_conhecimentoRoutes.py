import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="module")
def app_client():
	# Env mínimos antes de importar app.*
	os.environ.setdefault("KEY_CRYPT", "k")
	os.environ.setdefault("ALGORITHM", "HS256")
	os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
	os.environ.setdefault("DB_USER", "u")
	os.environ.setdefault("DB_PASSWORD", "p")
	os.environ.setdefault("DB_HOST", "localhost")
	os.environ.setdefault("DB_PORT", "5432")
	os.environ.setdefault("DB_NAME", "db")

	# Reimport limpo
	sys.modules.pop("app.main", None)
	sys.modules.pop("app.models", None)
	sys.modules.pop("app.dependencies", None)

	from app.models import Base  # noqa: E402

	engine = create_engine(
		"sqlite://",
		connect_args={"check_same_thread": False},
		poolclass=StaticPool,
	)
	event.listen(engine, "connect", lambda dbapi_conn, _: dbapi_conn.execute("PRAGMA foreign_keys=ON"))
	TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	Base.metadata.create_all(bind=engine)

	from app.main import app
	from app.dependencies import pegar_sessao, requer_admin

	# Override sessão
	def _override_session():
		db = TestingSessionLocal()
		try:
			yield db
		finally:
			db.close()

	app.dependency_overrides[pegar_sessao] = _override_session
	app.dependency_overrides[requer_admin] = lambda: {"admin": True}

	client = TestClient(app)

	try:
		yield client, TestingSessionLocal
	finally:
		app.dependency_overrides.clear()
		Base.metadata.drop_all(bind=engine)


def _criar_conhecimento(SessionLocal, nome="Python"):
	from app.models import Conhecimento
	db = SessionLocal()
	try:
		c = Conhecimento(nome=nome)
		db.add(c)
		db.commit()
		db.refresh(c)
		return c.id
	finally:
		db.close()


def test_listar_e_buscar_conhecimento(app_client):
	client, SessionLocal = app_client

	# Lista vazia
	r = client.get("/conhecimento/")
	assert r.status_code == 200
	assert r.json() == []

	# Cria e lista
	cid = _criar_conhecimento(SessionLocal, nome="Flask")
	r2 = client.get("/conhecimento/")
	assert r2.status_code == 200
	data = r2.json()
	assert isinstance(data, list) and len(data) == 1
	assert data[0]["nome"] == "Flask"

	# Buscar por id existente
	r3 = client.get(f"/conhecimento/{cid}")
	assert r3.status_code == 200
	assert r3.json().get("id") == cid

	# Buscar por id inexistente
	r4 = client.get("/conhecimento/999999")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Conhecimento não encontrado"


def test_cadastrar_e_duplicidade(app_client):
	client, _ = app_client

	payload = {"nome": "Python"}
	r = client.post("/conhecimento/cadastro", json=payload)
	assert r.status_code == 200
	assert "Conhecimento 'Python' cadastrado com sucesso" == r.json().get("message")

	# Duplicado case-insensitive
	r2 = client.post("/conhecimento/cadastro", json={"nome": "python"})
	assert r2.status_code == 400
	assert r2.json().get("detail") == "Conhecimento já cadastrado"


def test_atualizar_e_deletar_conhecimento(app_client):
	client, SessionLocal = app_client
	cid = _criar_conhecimento(SessionLocal, nome="Inicial")

	# Atualiza
	r = client.put(f"/conhecimento/atualizar/{cid}", json={"nome": "Atualizado"})
	assert r.status_code == 200
	assert r.json().get("message") == "Conhecimento 'Atualizado' atualizado com sucesso"

	# Atualizar inexistente
	r2 = client.put("/conhecimento/atualizar/999999", json={"nome": "X"})
	assert r2.status_code == 404
	assert r2.json().get("detail") == "Conhecimento não encontrado"

	# Deletar
	r3 = client.delete(f"/conhecimento/deletar/{cid}")
	assert r3.status_code == 200
	assert r3.json().get("message") == "Conhecimento 'Atualizado' deletado com sucesso"

	# Deletar inexistente
	r4 = client.delete("/conhecimento/deletar/999999")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Conhecimento não encontrado"

