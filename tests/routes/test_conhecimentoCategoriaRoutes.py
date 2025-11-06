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


def _seed_conhecimento_categoria(SessionLocal):
	from app.models import Conhecimento, Categoria
	db = SessionLocal()
	try:
		con = Conhecimento(nome="Python")
		cat = Categoria(nome="Backend")
		db.add_all([con, cat])
		db.commit()
		db.refresh(con)
		db.refresh(cat)
		return con.id, cat.id
	finally:
		db.close()


def test_listar_por_conhecimento_vazio(app_client):
	client, SessionLocal = app_client
	# Cria conhecimento sem relações
	from app.models import Conhecimento
	db = SessionLocal()
	try:
		c = Conhecimento(nome="SemCategoria")
		db.add(c); db.commit(); db.refresh(c)
		cid = c.id
	finally:
		db.close()

	r = client.get(f"/conhecimento-categoria/{cid}")
	assert r.status_code == 200
	assert r.json() == []


def test_criar_relacao_e_duplicado(app_client):
	client, SessionLocal = app_client
	conhecimento_id, categoria_id = _seed_conhecimento_categoria(SessionLocal)

	payload = {"conhecimento_id": conhecimento_id, "categoria_id": categoria_id, "peso": None}
	r = client.post("/conhecimento-categoria/", json=payload)
	assert r.status_code == 200
	body = r.json()
	assert body.get("id") is not None
	assert body.get("conhecimento_id") == conhecimento_id
	assert body.get("categoria_id") == categoria_id

	# Duplicado deve falhar (unique constraint)
	r2 = client.post("/conhecimento-categoria/", json=payload)
	assert r2.status_code == 400
	# detail depende do driver/SQLAlchemy, então checamos apenas o status


def test_remover_relacao_fluxo(app_client):
	client, SessionLocal = app_client
	conhecimento_id, categoria_id = _seed_conhecimento_categoria(SessionLocal)

	# Cria relação
	client.post("/conhecimento-categoria/", json={
		"conhecimento_id": conhecimento_id,
		"categoria_id": categoria_id,
		"peso": 5,
	})

	# Lista deve ter 1
	r1 = client.get(f"/conhecimento-categoria/{conhecimento_id}")
	assert r1.status_code == 200
	assert isinstance(r1.json(), list) and len(r1.json()) == 1

	# Remove
	r2 = client.delete(f"/conhecimento-categoria/{conhecimento_id}/{categoria_id}")
	assert r2.status_code == 200
	j = r2.json()
	assert j.get("status") == "removida"
	assert j.get("conhecimento_id") == conhecimento_id and j.get("categoria_id") == categoria_id

	# Lista agora vazia
	r3 = client.get(f"/conhecimento-categoria/{conhecimento_id}")
	assert r3.status_code == 200
	assert r3.json() == []

	# Remoção inexistente => 404
	r4 = client.delete(f"/conhecimento-categoria/{conhecimento_id}/{categoria_id}")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Relação não encontrada"

