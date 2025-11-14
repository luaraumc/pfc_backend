import os
import sys

import pytest
from .utils_test_routes import app_client_context, criar_categoria, criar_habilidade


@pytest.fixture(scope="module")
def app_client():
	"""Inicializa o TestClient com privilégios de admin para rotas de habilidade."""
	with app_client_context(override_admin=True) as ctx:
		yield ctx


def _criar_categoria(SessionLocal, nome="Backend"):
	"""Cria uma categoria de teste e retorna seu ID."""
	return criar_categoria(SessionLocal, nome=nome)


def _criar_habilidade(SessionLocal, nome="Python", categoria_id=None):
	"""Cria uma habilidade de teste e retorna seu ID."""
	return criar_habilidade(SessionLocal, nome=nome, categoria_id=categoria_id)


def test_listar_e_buscar_habilidade(app_client):
	"""Lista habilidades, cria uma, busca por ID e valida inexistente."""
	client, SessionLocal = app_client

	r = client.get("/habilidade/")
	assert r.status_code == 200
	assert r.json() == []

	cat_id = _criar_categoria(SessionLocal, nome="Dados")
	hid = _criar_habilidade(SessionLocal, nome="Pandas", categoria_id=cat_id)

	r2 = client.get("/habilidade/")
	assert r2.status_code == 200
	data = r2.json()
	assert isinstance(data, list) and len(data) == 1
	assert data[0]["nome"] == "Pandas"

	r3 = client.get(f"/habilidade/{hid}")
	assert r3.status_code == 200
	assert r3.json().get("id") == hid

	r4 = client.get("/habilidade/999999")
	assert r4.status_code == 404
	assert r4.json().get("detail") == "Habilidade não encontrada"


def test_listar_categorias_ordenadas(app_client):
	"""Cria categorias fora de ordem e verifica retorno ordenado por nome."""
	client, SessionLocal = app_client

	_ = _criar_categoria(SessionLocal, nome="Zeta")
	_ = _criar_categoria(SessionLocal, nome="Alpha")
	_ = _criar_categoria(SessionLocal, nome="Mid")

	r = client.get("/habilidade/categorias")
	assert r.status_code == 200
	nomes = [c["nome"] for c in r.json()]
	assert nomes == sorted(nomes)


def test_atualizar_habilidade_nome_e_categoria(app_client):
	"""Atualiza nome e categoria da habilidade e valida 404 para categoria inválida."""
	client, SessionLocal = app_client
	cat1 = _criar_categoria(SessionLocal, nome="Backend")
	cat2 = _criar_categoria(SessionLocal, nome="Data")
	hid = _criar_habilidade(SessionLocal, nome="OldName", categoria_id=cat1)

	r = client.put(
		f"/habilidade/atualizar/{hid}",
		json={"nome": "NewName", "categoria_id": cat2},
	)
	assert r.status_code == 200
	body = r.json()
	assert body.get("nome") == "NewName"
	assert body.get("categoria_id") == cat2

	r2 = client.put(
		f"/habilidade/atualizar/{hid}",
		json={"categoria_id": 999999},
	)
	assert r2.status_code == 404
	assert r2.json().get("detail") == "Habilidade não encontrada"


def test_deletar_habilidade_sucesso_e_404(app_client):
	"""Deleta uma habilidade e confirma 404 ao tentar deletar novamente."""
	client, SessionLocal = app_client
	cat = _criar_categoria(SessionLocal, nome="Apps")
	hid = _criar_habilidade(SessionLocal, nome="Flutter", categoria_id=cat)

	r = client.delete(f"/habilidade/deletar/{hid}")
	assert r.status_code == 200
	msg = r.json().get("message", "")
	assert "Habilidade 'Flutter' deletada com sucesso" == msg

	r2 = client.delete(f"/habilidade/deletar/{hid}")
	assert r2.status_code == 404
	assert r2.json().get("detail") == "Habilidade não encontrada"

