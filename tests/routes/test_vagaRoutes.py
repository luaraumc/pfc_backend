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
	for m in ("app.main", "app.models", "app.dependencies"):
		sys.modules.pop(m, None)

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


def _criar_carreira(SessionLocal, nome="Dados"):
	from app.models import Carreira
	db = SessionLocal()
	try:
		c = Carreira(nome=nome, descricao="d")
		db.add(c); db.commit(); db.refresh(c)
		return c.id
	finally:
		db.close()


def _criar_categoria(SessionLocal, nome="Backend"):
	from app.models import Categoria
	db = SessionLocal()
	try:
		cat = Categoria(nome=nome)
		db.add(cat); db.commit(); db.refresh(cat)
		return cat.id
	finally:
		db.close()


def _criar_habilidade(SessionLocal, nome="Python", categoria_id=None):
	from app.models import Habilidade
	assert categoria_id is not None
	db = SessionLocal()
	try:
		h = Habilidade(nome=nome, categoria_id=categoria_id)
		db.add(h); db.commit(); db.refresh(h)
		return h.id
	finally:
		db.close()


def _buscar_carreira_habilidade(SessionLocal, carreira_id, habilidade_id):
	from app.models import CarreiraHabilidade
	db = SessionLocal()
	try:
		return db.query(CarreiraHabilidade).filter_by(carreira_id=carreira_id, habilidade_id=habilidade_id).first()
	finally:
		db.close()


def test_listar_e_cadastrar_vaga_e_duplicidade(app_client):
	client, SessionLocal = app_client
	car_id = _criar_carreira(SessionLocal)

	# Lista vazia
	r0 = client.get("/vaga/")
	assert r0.status_code == 200 and r0.json() == []

	payload = {"titulo": "Dev", "descricao": "Descricao unica ABC", "carreira_id": car_id}
	r1 = client.post("/vaga/cadastro", json=payload)
	assert r1.status_code == 200
	body = r1.json()
	assert body.get("id") and body.get("titulo") == "Dev"
	assert body.get("carreira_id") == car_id

	# Lista tem 1 e traz carreira_nome
	r2 = client.get("/vaga/")
	assert r2.status_code == 200
	lista = r2.json()
	assert len(lista) == 1 and lista[0]["carreira_id"] == car_id
	assert isinstance(lista[0].get("carreira_nome"), (str, type(None)))

	# Duplicidade por descricao -> 409
	r_dup = client.post("/vaga/cadastro", json=payload)
	assert r_dup.status_code == 409
	assert r_dup.json().get("detail") == "Já existe uma vaga com a mesma descrição."


def test_preview_habilidades_monkeypatched(app_client, monkeypatch):
	client, SessionLocal = app_client
	car_id = _criar_carreira(SessionLocal)
	cat_id = _criar_categoria(SessionLocal, "Backend")
	existing_hid = _criar_habilidade(SessionLocal, "Python", categoria_id=cat_id)

	# Cadastra vaga
	r_cad = client.post("/vaga/cadastro", json={
		"titulo": "Vaga P",
		"descricao": "qualquer descricao",
		"carreira_id": car_id,
	})
	vaga_id = r_cad.json()["id"]

	# Patch de extração para evitar chamadas externas
	import app.services.extracao as extr

	def fake_extract(desc, session=None):
		return [
			{"nome": "Python", "categoria_sugerida": "Backend"},
			{"nome": "Flask", "categoria_sugerida": "Backend"},
		]

	def fake_norm(name, session=None):
		return name

	monkeypatch.setattr(extr, "extrair_habilidades_descricao", fake_extract)
	monkeypatch.setattr(extr, "normalizar_habilidade", fake_norm)

	r = client.get(f"/vaga/{vaga_id}/preview-habilidades")
	assert r.status_code == 200
	itens = r.json()
	# Deve conter Python existente (com habilidade_id preenchido) e Flask novo (habilidade_id vazio, categoria_id de Backend)
	names = {i["nome"] for i in itens}
	assert "Python" in names and "Flask" in names
	python_it = next(i for i in itens if i["nome"] == "Python")
	flask_it = next(i for i in itens if i["nome"] == "Flask")
	assert python_it.get("habilidade_id") == existing_hid
	assert flask_it.get("habilidade_id") in ("", None)
	assert flask_it.get("categoria_id") == cat_id


def test_confirmar_habilidades_cria_e_incrementa(app_client):
	client, SessionLocal = app_client
	car_id = _criar_carreira(SessionLocal)
	cat_id = _criar_categoria(SessionLocal, "Backend")
	existing_hid = _criar_habilidade(SessionLocal, "Python", categoria_id=cat_id)

	# Cadastra vaga
	r_cad = client.post("/vaga/cadastro", json={
		"titulo": "Vaga C",
		"descricao": "texto unico confirm",
		"carreira_id": car_id,
	})
	vaga_id = r_cad.json()["id"]

	payload = {
		"habilidades": [
			{"nome": "Python"},
			{"nome": "Flask", "categoria_sugerida": "Backend"},
		]
	}
	r = client.post(f"/vaga/{vaga_id}/confirmar-habilidades", json=payload)
	assert r.status_code == 200
	body = r.json()
	assert "Flask" in body.get("habilidades_criadas", [])
	assert "Python" in body.get("habilidades_ja_existiam", [])

	# Frequências da carreira devem ser 1 para ambas
	from app.models import Habilidade
	db = SessionLocal()
	try:
		flask_id = db.query(Habilidade.id).filter(Habilidade.nome == "Flask").scalar()
	finally:
		db.close()

	rel_py = _buscar_carreira_habilidade(SessionLocal, car_id, existing_hid)
	rel_fl = _buscar_carreira_habilidade(SessionLocal, car_id, flask_id)
	assert rel_py and rel_py.frequencia == 1
	assert rel_fl and rel_fl.frequencia == 1


def test_remover_relacao_vaga_habilidade(app_client):
	client, SessionLocal = app_client
	car_id = _criar_carreira(SessionLocal)
	cat_id = _criar_categoria(SessionLocal, "Backend")
	hid = _criar_habilidade(SessionLocal, "Django", categoria_id=cat_id)

	# Cadastra vaga e confirma relação
	r_cad = client.post("/vaga/cadastro", json={
		"titulo": "Vaga R",
		"descricao": "texto unico remover",
		"carreira_id": car_id,
	})
	vaga_id = r_cad.json()["id"]

	payload = {"habilidades": [{"nome": "Django"}]}
	client.post(f"/vaga/{vaga_id}/confirmar-habilidades", json=payload)

	# Remove relação
	r = client.delete(f"/vaga/{vaga_id}/habilidades/{hid}")
	assert r.status_code == 200
	assert r.json().get("status") == "removido"

	# Remover novamente => 404
	r2 = client.delete(f"/vaga/{vaga_id}/habilidades/{hid}")
	assert r2.status_code == 404
	assert r2.json().get("detail") == "Relação não encontrada"


def test_excluir_vaga_decrementa_frequencias(app_client):
	client, SessionLocal = app_client
	car_id = _criar_carreira(SessionLocal)
	cat_id = _criar_categoria(SessionLocal, "Backend")
	hid1 = _criar_habilidade(SessionLocal, "Node.js", categoria_id=cat_id)
	hid2 = _criar_habilidade(SessionLocal, "React", categoria_id=cat_id)

	# Cadastra vaga e confirma duas habilidades
	r_cad = client.post("/vaga/cadastro", json={
		"titulo": "Vaga D",
		"descricao": "texto unico deletar",
		"carreira_id": car_id,
	})
	vaga_id = r_cad.json()["id"]

	client.post(f"/vaga/{vaga_id}/confirmar-habilidades", json={
		"habilidades": [{"nome": "Node.js"}, {"nome": "React"}]
	})

	# Exclui vaga
	r = client.delete(f"/vaga/{vaga_id}")
	assert r.status_code == 200
	assert r.json().get("status") == "excluida"

	# As relações CarreiraHabilidade devem ter sido removidas (freq 1 -> 0 remove)
	rel1 = _buscar_carreira_habilidade(SessionLocal, car_id, hid1)
	rel2 = _buscar_carreira_habilidade(SessionLocal, car_id, hid2)
	assert rel1 is None and rel2 is None

