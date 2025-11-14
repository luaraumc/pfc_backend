import os
import sys

import pytest
from .utils_test_routes import app_client_context, criar_curso, criar_conhecimento


@pytest.fixture(scope="module")
def app_client():
	"""Inicializa o TestClient com privilégios de admin para rotas protegidas."""
	with app_client_context(override_admin=True) as ctx:
		yield ctx


def _criar_curso(SessionLocal, nome="ADS", desc="desc"):
	"""Cria um curso de teste e retorna seu ID."""
	return criar_curso(SessionLocal, nome=nome, desc=desc)


def _criar_conhecimento(SessionLocal, nome="Python"):
	"""Cria um conhecimento de teste e retorna seu ID."""
	return criar_conhecimento(SessionLocal, nome=nome)


def test_listar_e_buscar_curso(app_client):
	"""Lista cursos, cria um, busca por ID e valida inexistente."""
	client, SessionLocal = app_client

	r = client.get("/curso/")
	assert r.status_code == 200
	assert r.json() == []

	cid = _criar_curso(SessionLocal, nome="Sistemas", desc="d")
	r2 = client.get("/curso/")
	assert r2.status_code == 200
	data = r2.json()
	assert isinstance(data, list) and len(data) == 1
	assert data[0]["nome"] == "Sistemas"

	r3 = client.get(f"/curso/{cid}")
	assert r3.status_code == 200
	assert r3.json().get("id") == cid

	r4 = client.get("/curso/999999")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Curso não encontrado"


def test_cadastro_e_duplicidade(app_client):
	"""Cadastra um curso e valida erro ao tentar duplicar."""
	client, _ = app_client

	payload = {"nome": "ADS", "descricao": "desc"}
	r = client.post("/curso/cadastro", json=payload)
	assert r.status_code == 200
	assert r.json().get("message") == "Curso cadastrado com sucesso: ADS"

	r2 = client.post("/curso/cadastro", json=payload)
	assert r2.status_code == 400
	assert r2.json().get("detail") == "curso já cadastrado"


def test_atualizar_e_deletar_curso(app_client):
	"""Atualiza e deleta curso e valida respostas para IDs inexistentes."""
	client, SessionLocal = app_client
	cid = _criar_curso(SessionLocal, nome="Inicial", desc="d")

	r = client.put(f"/curso/atualizar/{cid}", json={"nome": "Atualizado", "descricao": "n"})
	assert r.status_code == 200
	assert r.json().get("message") == "Curso atualizado com sucesso: Atualizado"

	r2 = client.put("/curso/atualizar/999999", json={"nome": "X", "descricao": "y"})
	assert r2.status_code == 404
	assert r2.json().get("detail") == "Curso não encontrado"

	r3 = client.delete(f"/curso/deletar/{cid}")
	assert r3.status_code == 200
	assert r3.json().get("message") == "Curso deletado com sucesso: Atualizado"

	r4 = client.delete("/curso/deletar/999999")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Curso não encontrado"


def test_conhecimentos_do_curso_fluxo(app_client):
	"""Gerencia conhecimentos do curso: lista, adiciona, evita duplicar, remove e valida 404."""
	client, SessionLocal = app_client
	curso_id = _criar_curso(SessionLocal, nome="Curso K", desc="d")
	conhecimento_id = _criar_conhecimento(SessionLocal, nome="K1")

	r0 = client.get(f"/curso/{curso_id}/conhecimentos")
	assert r0.status_code == 200
	assert r0.json() == []

	r1 = client.post(f"/curso/{curso_id}/adicionar-conhecimento/{conhecimento_id}")
	assert r1.status_code == 200
	body = r1.json()
	assert body.get("id") is not None
	assert body.get("curso_id") == curso_id
	assert body.get("conhecimento_id") == conhecimento_id

	r2 = client.post(f"/curso/{curso_id}/adicionar-conhecimento/{conhecimento_id}")
	assert r2.status_code == 400
	assert r2.json().get("detail") == "Conhecimento já adicionado ao curso"

	r3 = client.get(f"/curso/{curso_id}/conhecimentos")
	assert r3.status_code == 200
	assert isinstance(r3.json(), list) and len(r3.json()) == 1

	r4 = client.delete(f"/curso/{curso_id}/remover-conhecimento/{conhecimento_id}")
	assert r4.status_code == 200
	body2 = r4.json()
	assert body2.get("curso_id") == curso_id and body2.get("conhecimento_id") == conhecimento_id

	r5 = client.get(f"/curso/{curso_id}/conhecimentos")
	assert r5.status_code == 200
	assert r5.json() == []

	r6 = client.delete(f"/curso/{curso_id}/remover-conhecimento/{conhecimento_id}")
	assert r6.status_code == 404
	assert r6.json().get("detail") == "Relação curso-conhecimento não encontrada"

