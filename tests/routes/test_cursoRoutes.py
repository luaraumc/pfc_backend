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


def _criar_curso(SessionLocal, nome="ADS", desc="desc"):
	from app.models import Curso
	db = SessionLocal()
	try:
		c = Curso(nome=nome, descricao=desc)
		db.add(c)
		db.commit()
		db.refresh(c)
		return c.id
	finally:
		db.close()


def _criar_conhecimento(SessionLocal, nome="Python"):
	from app.models import Conhecimento
	db = SessionLocal()
	try:
		k = Conhecimento(nome=nome)
		db.add(k)
		db.commit()
		db.refresh(k)
		return k.id
	finally:
		db.close()


def test_listar_e_buscar_curso(app_client):
	client, SessionLocal = app_client

	# Lista vazia
	r = client.get("/curso/")
	assert r.status_code == 200
	assert r.json() == []

	# Cria e lista
	cid = _criar_curso(SessionLocal, nome="Sistemas", desc="d")
	r2 = client.get("/curso/")
	assert r2.status_code == 200
	data = r2.json()
	assert isinstance(data, list) and len(data) == 1
	assert data[0]["nome"] == "Sistemas"

	# Buscar por id existente
	r3 = client.get(f"/curso/{cid}")
	assert r3.status_code == 200
	assert r3.json().get("id") == cid

	# Buscar por id inexistente
	r4 = client.get("/curso/999999")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Curso não encontrado"


def test_cadastro_e_duplicidade(app_client):
	client, _ = app_client

	payload = {"nome": "ADS", "descricao": "desc"}
	r = client.post("/curso/cadastro", json=payload)
	assert r.status_code == 200
	assert r.json().get("message") == "Curso cadastrado com sucesso: ADS"

	# Duplicado
	r2 = client.post("/curso/cadastro", json=payload)
	assert r2.status_code == 400
	assert r2.json().get("detail") == "curso já cadastrado"


def test_atualizar_e_deletar_curso(app_client):
	client, SessionLocal = app_client
	cid = _criar_curso(SessionLocal, nome="Inicial", desc="d")

	# Atualiza
	r = client.put(f"/curso/atualizar/{cid}", json={"nome": "Atualizado", "descricao": "n"})
	assert r.status_code == 200
	assert r.json().get("message") == "Curso atualizado com sucesso: Atualizado"

	# Atualizar inexistente
	r2 = client.put("/curso/atualizar/999999", json={"nome": "X", "descricao": "y"})
	assert r2.status_code == 404
	assert r2.json().get("detail") == "Curso não encontrado"

	# Deletar
	r3 = client.delete(f"/curso/deletar/{cid}")
	assert r3.status_code == 200
	assert r3.json().get("message") == "Curso deletado com sucesso: Atualizado"

	# Deletar inexistente
	r4 = client.delete("/curso/deletar/999999")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Curso não encontrado"


def test_conhecimentos_do_curso_fluxo(app_client):
	client, SessionLocal = app_client
	curso_id = _criar_curso(SessionLocal, nome="Curso K", desc="d")
	conhecimento_id = _criar_conhecimento(SessionLocal, nome="K1")

	# Lista vazia
	r0 = client.get(f"/curso/{curso_id}/conhecimentos")
	assert r0.status_code == 200
	assert r0.json() == []

	# Adiciona relação
	r1 = client.post(f"/curso/{curso_id}/adicionar-conhecimento/{conhecimento_id}")
	assert r1.status_code == 200
	body = r1.json()
	assert body.get("id") is not None
	assert body.get("curso_id") == curso_id
	assert body.get("conhecimento_id") == conhecimento_id

	# Duplicado => 400
	r2 = client.post(f"/curso/{curso_id}/adicionar-conhecimento/{conhecimento_id}")
	assert r2.status_code == 400
	assert r2.json().get("detail") == "Conhecimento já adicionado ao curso"

	# Lista com 1 item
	r3 = client.get(f"/curso/{curso_id}/conhecimentos")
	assert r3.status_code == 200
	assert isinstance(r3.json(), list) and len(r3.json()) == 1

	# Remove relação
	r4 = client.delete(f"/curso/{curso_id}/remover-conhecimento/{conhecimento_id}")
	assert r4.status_code == 200
	body2 = r4.json()
	assert body2.get("curso_id") == curso_id and body2.get("conhecimento_id") == conhecimento_id

	# Lista vazia novamente
	r5 = client.get(f"/curso/{curso_id}/conhecimentos")
	assert r5.status_code == 200
	assert r5.json() == []

	# Remover inexistente => 404
	r6 = client.delete(f"/curso/{curso_id}/remover-conhecimento/{conhecimento_id}")
	assert r6.status_code == 404
	assert r6.json().get("detail") == "Relação curso-conhecimento não encontrada"

