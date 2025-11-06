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


def _criar_categoria(SessionLocal, nome="Backend"):
	from app.models import Categoria
	db = SessionLocal()
	try:
		c = Categoria(nome=nome)
		db.add(c)
		db.commit()
		db.refresh(c)
		return c.id
	finally:
		db.close()


def _criar_habilidade(SessionLocal, nome="Python", categoria_id=None):
	from app.models import Habilidade
	if categoria_id is None:
		raise AssertionError("categoria_id é obrigatório para criar habilidade")
	db = SessionLocal()
	try:
		h = Habilidade(nome=nome, categoria_id=categoria_id)
		db.add(h)
		db.commit()
		db.refresh(h)
		return h.id
	finally:
		db.close()


def test_listar_e_buscar_habilidade(app_client):
	client, SessionLocal = app_client

	# Lista vazia
	r = client.get("/habilidade/")
	assert r.status_code == 200
	assert r.json() == []

	# Seed: categoria + habilidade
	cat_id = _criar_categoria(SessionLocal, nome="Dados")
	hid = _criar_habilidade(SessionLocal, nome="Pandas", categoria_id=cat_id)

	# Lista com 1
	r2 = client.get("/habilidade/")
	assert r2.status_code == 200
	data = r2.json()
	assert isinstance(data, list) and len(data) == 1
	assert data[0]["nome"] == "Pandas"

	# Buscar existente
	r3 = client.get(f"/habilidade/{hid}")
	assert r3.status_code == 200
	assert r3.json().get("id") == hid

	# Buscar inexistente
	r4 = client.get("/habilidade/999999")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Habilidade não encontrada"


def test_listar_categorias_ordenadas(app_client):
	client, SessionLocal = app_client
	# Cria categorias fora de ordem
	_ = _criar_categoria(SessionLocal, nome="Zeta")
	_ = _criar_categoria(SessionLocal, nome="Alpha")
	_ = _criar_categoria(SessionLocal, nome="Mid")

	r = client.get("/habilidade/categorias")
	assert r.status_code == 200
	nomes = [c["nome"] for c in r.json()]
	assert nomes == sorted(nomes)


def test_atualizar_habilidade_nome_e_categoria(app_client):
	client, SessionLocal = app_client
	cat1 = _criar_categoria(SessionLocal, nome="Backend")
	cat2 = _criar_categoria(SessionLocal, nome="Data")
	hid = _criar_habilidade(SessionLocal, nome="OldName", categoria_id=cat1)

	# Atualiza nome e categoria
	r = client.put(
		f"/habilidade/atualizar/{hid}",
		json={"nome": "NewName", "categoria_id": cat2},
	)
	assert r.status_code == 200
	body = r.json()
	assert body.get("nome") == "NewName"
	assert body.get("categoria_id") == cat2

	# Tenta atualizar com categoria inexistente => service retorna None => rota 404
	r2 = client.put(
		f"/habilidade/atualizar/{hid}",
		json={"categoria_id": 999999},
	)
	assert r2.status_code == 404
	assert r2.json().get("detail") == "Habilidade não encontrada"


def test_deletar_habilidade_sucesso_e_404(app_client):
	client, SessionLocal = app_client
	cat = _criar_categoria(SessionLocal, nome="Apps")
	hid = _criar_habilidade(SessionLocal, nome="Flutter", categoria_id=cat)

	# Deletar
	r = client.delete(f"/habilidade/deletar/{hid}")
	assert r.status_code == 200
	msg = r.json().get("message", "")
	assert "Habilidade 'Flutter' deletada com sucesso" == msg

	# Deletar inexistente
	r2 = client.delete(f"/habilidade/deletar/{hid}")
	assert r2.status_code == 404
	assert r2.json().get("detail") == "Habilidade não encontrada"

