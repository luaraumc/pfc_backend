import os
import sys

import pytest
from .utils_test_routes import app_client_context, seed_conhecimento_categoria


@pytest.fixture(scope="module")
def app_client():
	"""Inicializa o TestClient com admin para rotas de criação/remoção."""
	with app_client_context(override_admin=True) as ctx:
		yield ctx


def _seed_conhecimento_categoria(SessionLocal):
	"""Semeia conhecimento e categoria usando utilitário compartilhado."""
	return seed_conhecimento_categoria(SessionLocal)


def test_listar_por_conhecimento_vazio(app_client):
	"""Cria conhecimento sem relações e verifica lista vazia de categorias."""
	client, SessionLocal = app_client
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
	"""Cria relação conhecimento-categoria e valida falha em duplicidade."""
	client, SessionLocal = app_client
	conhecimento_id, categoria_id = _seed_conhecimento_categoria(SessionLocal)

	payload = {"conhecimento_id": conhecimento_id, "categoria_id": categoria_id, "peso": None}
	r = client.post("/conhecimento-categoria/", json=payload)
	assert r.status_code == 200
	body = r.json()
	assert body.get("id") is not None
	assert body.get("conhecimento_id") == conhecimento_id
	assert body.get("categoria_id") == categoria_id

	r2 = client.post("/conhecimento-categoria/", json=payload)
	assert r2.status_code == 400


def test_remover_relacao_fluxo(app_client):
	"""Cria, lista e remove a relação; valida vazia e 404 na remoção repetida."""
	client, SessionLocal = app_client
	conhecimento_id, categoria_id = _seed_conhecimento_categoria(SessionLocal)

	client.post("/conhecimento-categoria/", json={
		"conhecimento_id": conhecimento_id,
		"categoria_id": categoria_id,
		"peso": 2,
	})

	r1 = client.get(f"/conhecimento-categoria/{conhecimento_id}")
	assert r1.status_code == 200
	assert isinstance(r1.json(), list) and len(r1.json()) == 1

	r2 = client.delete(f"/conhecimento-categoria/{conhecimento_id}/{categoria_id}")
	assert r2.status_code == 200
	j = r2.json()
	assert j.get("status") == "removida"
	assert j.get("conhecimento_id") == conhecimento_id and j.get("categoria_id") == categoria_id

	r3 = client.get(f"/conhecimento-categoria/{conhecimento_id}")
	assert r3.status_code == 200
	assert r3.json() == []

	r4 = client.delete(f"/conhecimento-categoria/{conhecimento_id}/{categoria_id}")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Relação não encontrada"

