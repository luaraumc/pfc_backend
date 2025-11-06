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
	# Override admin para autorizar rotas protegidas
	app.dependency_overrides[requer_admin] = lambda: {"admin": True}

	client = TestClient(app)

	try:
		yield client, TestingSessionLocal
	finally:
		app.dependency_overrides.clear()
		Base.metadata.drop_all(bind=engine)


def _criar_carreira(SessionLocal, nome="Carreira X", desc="desc"):
	from app.models import Carreira
	db = SessionLocal()
	try:
		c = Carreira(nome=nome, descricao=desc)
		db.add(c)
		db.commit()
		db.refresh(c)
		return c.id
	finally:
		db.close()


def test_listar_e_buscar_carreira(app_client):
	client, SessionLocal = app_client

	# Lista vazia
	r = client.get("/carreira/")
	assert r.status_code == 200
	assert r.json() == []

	# Cria e lista
	cid = _criar_carreira(SessionLocal, nome="Dados")
	r2 = client.get("/carreira/")
	assert r2.status_code == 200
	data = r2.json()
	assert isinstance(data, list) and len(data) == 1
	assert data[0]["nome"] == "Dados"

	# Buscar por id existente
	r3 = client.get(f"/carreira/{cid}")
	assert r3.status_code == 200
	assert r3.json().get("id") == cid

	# Buscar por id inexistente
	r4 = client.get("/carreira/999999")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Carreira não encontrada"


def test_cadastro_e_duplicidade(app_client):
	client, _ = app_client

	payload = {"nome": "Engenharia", "descricao": "desc"}
	r = client.post("/carreira/cadastro", json=payload)
	assert r.status_code == 200
	assert "Carreira cadastrada com sucesso" in r.json().get("message", "")

	# Duplicado
	r2 = client.post("/carreira/cadastro", json=payload)
	assert r2.status_code == 400
	assert r2.json().get("detail") == "Carreira já cadastrada"


def test_atualizar_e_deletar_carreira(app_client):
	client, SessionLocal = app_client
	cid = _criar_carreira(SessionLocal, nome="Inicial", desc="d")

	# Atualiza
	r = client.put(f"/carreira/atualizar/{cid}", json={"nome": "Atualizada", "descricao": "nova"})
	assert r.status_code == 200
	assert "Carreira atualizada com sucesso" in r.json().get("message", "")

	# Atualizar inexistente
	r2 = client.put("/carreira/atualizar/999999", json={"nome": "X", "descricao": "y"})
	assert r2.status_code == 404
	assert r2.json().get("detail") == "Carreira não encontrada"

	# Deletar
	r3 = client.delete(f"/carreira/deletar/{cid}")
	assert r3.status_code == 200
	assert "Carreira deletada com sucesso" in r3.json().get("message", "")

	# Deletar inexistente
	r4 = client.delete("/carreira/deletar/999999")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Carreira não encontrada"


def test_habilidades_listar_e_remover(app_client):
	client, SessionLocal = app_client
	from app.models import Categoria, Habilidade, CarreiraHabilidade

	# Prepara carreira e habilidade
	cid = _criar_carreira(SessionLocal, nome="Car Habs")
	db = SessionLocal()
	try:
		cat = Categoria(nome="Backend")
		db.add(cat); db.commit(); db.refresh(cat)

		hab = Habilidade(nome="Python", categoria_id=cat.id)
		db.add(hab); db.commit(); db.refresh(hab)

		rel = CarreiraHabilidade(carreira_id=cid, habilidade_id=hab.id)
		db.add(rel); db.commit(); db.refresh(rel)
		hid = hab.id
	finally:
		db.close()

	# Lista habilidades da carreira
	r = client.get(f"/carreira/{cid}/habilidades")
	assert r.status_code == 200
	lista = r.json()
	assert isinstance(lista, list) and len(lista) == 1

	# Remove relação
	r2 = client.delete(f"/carreira/{cid}/remover-habilidade/{hid}")
	assert r2.status_code == 200

	# Lista novamente deve estar vazia
	r3 = client.get(f"/carreira/{cid}/habilidades")
	assert r3.status_code == 200
	assert r3.json() == []

	# Remoção inexistente
	r4 = client.delete(f"/carreira/{cid}/remover-habilidade/{hid}")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Relação carreira-habilidade não encontrada"

