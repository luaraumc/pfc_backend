import os
import sys

import pytest
from .utils_test_routes import app_client_context, criar_carreira


@pytest.fixture(scope="module")
def app_client():
	"""Inicializa o TestClient com privilégio admin para rotas protegidas."""
	with app_client_context(override_admin=True) as ctx:
		yield ctx


def _criar_carreira(SessionLocal, nome="Carreira X", desc="desc"):
	"""Cria uma carreira de teste e retorna seu ID."""
	return criar_carreira(SessionLocal, nome=nome, desc=desc)


def test_listar_e_buscar_carreira(app_client):
	"""Lista carreiras, cria uma, busca por ID e valida inexistente."""
	client, SessionLocal = app_client
	r = client.get("/carreira/")
	assert r.status_code == 200
	assert r.json() == []

	cid = _criar_carreira(SessionLocal, nome="Dados")
	r2 = client.get("/carreira/")
	assert r2.status_code == 200
	data = r2.json()
	assert isinstance(data, list) and len(data) == 1
	assert data[0]["nome"] == "Dados"

	r3 = client.get(f"/carreira/{cid}")
	assert r3.status_code == 200
	assert r3.json().get("id") == cid

	r4 = client.get("/carreira/999999")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Carreira não encontrada"


def test_cadastro_e_duplicidade(app_client):
	"""Cadastra uma carreira e verifica erro ao repetir o cadastro."""
	client, _ = app_client

	payload = {"nome": "Engenharia", "descricao": "desc"}
	r = client.post("/carreira/cadastro", json=payload)
	assert r.status_code == 200
	assert "Carreira cadastrada com sucesso" in r.json().get("message", "")

	r2 = client.post("/carreira/cadastro", json=payload)
	assert r2.status_code == 400
	assert r2.json().get("detail") == "Carreira já cadastrada"


def test_atualizar_e_deletar_carreira(app_client):
	"""Atualiza e exclui uma carreira e valida erros para IDs inexistentes."""
	client, SessionLocal = app_client
	cid = _criar_carreira(SessionLocal, nome="Inicial", desc="d")

	r = client.put(f"/carreira/atualizar/{cid}", json={"nome": "Atualizada", "descricao": "nova"})
	assert r.status_code == 200
	assert "Carreira atualizada com sucesso" in r.json().get("message", "")

	r2 = client.put("/carreira/atualizar/999999", json={"nome": "X", "descricao": "y"})
	assert r2.status_code == 404
	assert r2.json().get("detail") == "Carreira não encontrada"

	r3 = client.delete(f"/carreira/deletar/{cid}")
	assert r3.status_code == 200
	assert "Carreira deletada com sucesso" in r3.json().get("message", "")

	r4 = client.delete("/carreira/deletar/999999")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Carreira não encontrada"


def test_habilidades_listar_e_remover(app_client):
	"""Lista habilidades da carreira, remove a relação e valida respostas."""
	client, SessionLocal = app_client
	from app.models import Categoria, Habilidade, CarreiraHabilidade

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

	r = client.get(f"/carreira/{cid}/habilidades")
	assert r.status_code == 200
	lista = r.json()
	assert isinstance(lista, list) and len(lista) == 1

	r2 = client.delete(f"/carreira/{cid}/remover-habilidade/{hid}")
	assert r2.status_code == 200

	r3 = client.get(f"/carreira/{cid}/habilidades")
	assert r3.status_code == 200
	assert r3.json() == []

	r4 = client.delete(f"/carreira/{cid}/remover-habilidade/{hid}")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Relação carreira-habilidade não encontrada"

