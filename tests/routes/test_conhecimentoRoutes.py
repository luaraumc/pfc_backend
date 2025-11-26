import os
import sys

import pytest
from .utils_test_routes import app_client_context, criar_conhecimento


@pytest.fixture(scope="module")
def app_client():
	"""Inicializa o TestClient com privilégios de admin para rotas protegidas."""
	with app_client_context(override_admin=True) as ctx:
		yield ctx


def _criar_conhecimento(SessionLocal, nome="Python"):
	"""Cria um conhecimento de teste e retorna seu ID."""
	return criar_conhecimento(SessionLocal, nome=nome)


def test_listar_e_buscar_conhecimento(app_client):
	"""Lista conhecimentos, cria um, busca por ID e valida inexistente."""
	client, SessionLocal = app_client

	r = client.get("/conhecimento/")
	assert r.status_code == 200
	assert r.json() == []

	cid = _criar_conhecimento(SessionLocal, nome="Flask")
	r2 = client.get("/conhecimento/")
	assert r2.status_code == 200
	data = r2.json()
	assert isinstance(data, list) and len(data) == 1
	assert data[0]["nome"] == "Flask"

	r3 = client.get(f"/conhecimento/{cid}")
	assert r3.status_code == 200
	assert r3.json().get("id") == cid

	r4 = client.get("/conhecimento/999999")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Conhecimento não encontrado"


def test_cadastrar_e_duplicidade(app_client):
	"""Cadastra conhecimento e verifica erro ao tentar duplicar (case-insensitive)."""
	client, _ = app_client

	payload = {"nome": "Python"}
	r = client.post("/conhecimento/cadastro", json=payload)
	assert r.status_code == 200
	assert "Conhecimento 'Python' cadastrado com sucesso" == r.json().get("message")

	r2 = client.post("/conhecimento/cadastro", json={"nome": "python"})
	assert r2.status_code == 400
	assert r2.json().get("detail") == "Conhecimento já cadastrado"


def test_atualizar_e_deletar_conhecimento(app_client):
	"""Atualiza e deleta conhecimento e valida respostas para IDs inexistentes."""
	client, SessionLocal = app_client
	cid = _criar_conhecimento(SessionLocal, nome="Inicial")

	r = client.put(f"/conhecimento/atualizar/{cid}", json={"nome": "Atualizado"})
	assert r.status_code == 200
	assert r.json().get("message") == "Conhecimento 'Atualizado' atualizado com sucesso"

	r2 = client.put("/conhecimento/atualizar/999999", json={"nome": "X"})
	assert r2.status_code == 404
	assert r2.json().get("detail") == "Conhecimento não encontrado"

	r3 = client.delete(f"/conhecimento/deletar/{cid}")
	assert r3.status_code == 200
	assert r3.json().get("message") == "Conhecimento 'Atualizado' deletado com sucesso"

	r4 = client.delete("/conhecimento/deletar/999999")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Conhecimento não encontrado"

