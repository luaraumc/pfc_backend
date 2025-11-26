import os
import sys

import pytest
from .utils_test_routes import app_client_context, buscar_carreira_habilidade


@pytest.fixture(scope="module")
def app_client():
	"""Fixture que fornece cliente autenticado como admin para testar rotas de vaga."""
	with app_client_context(override_admin=True) as ctx:
		yield ctx


def _criar_carreira(SessionLocal, nome="Dados"):
	"""Cria uma carreira com nome único para uso nos testes."""
	from app.models import Carreira
	db = SessionLocal()
	try:
		count = db.query(Carreira).count() if hasattr(db, "query") else 0
		c = Carreira(nome=f"{nome}{count+1}", descricao="d")
		db.add(c); db.commit(); db.refresh(c)
		return c.id
	finally:
		db.close()


def _criar_categoria(SessionLocal, nome="Backend"):
	"""Cria uma categoria com nome único para uso nos testes."""
	from app.models import Categoria
	db = SessionLocal()
	try:
		count = db.query(Categoria).count() if hasattr(db, "query") else 0
		cat = Categoria(nome=f"{nome}{count+1}")
		db.add(cat); db.commit(); db.refresh(cat)
		return cat.id
	finally:
		db.close()


def _criar_habilidade(SessionLocal, nome="Python", categoria_id=None):
	"""Cria uma habilidade associada a uma categoria para uso nos testes."""
	from app.models import Habilidade
	assert categoria_id is not None
	db = SessionLocal()
	try:
		count = db.query(Habilidade).count() if hasattr(db, "query") else 0
		h = Habilidade(nome=f"{nome}{count+1}", categoria_id=categoria_id)
		db.add(h); db.commit(); db.refresh(h)
		return h.id
	finally:
		db.close()


def _buscar_carreira_habilidade(SessionLocal, carreira_id, habilidade_id):
	"""Busca a relação Carreira-Habilidade no banco para validações de teste."""
	return buscar_carreira_habilidade(SessionLocal, carreira_id, habilidade_id)


def test_listar_e_cadastrar_vaga_e_duplicidade(app_client):
	"""Verifica listagem vazia, cadastro de vaga e erro de duplicidade por descrição."""
	client, SessionLocal = app_client
	car_id = _criar_carreira(SessionLocal)

	r0 = client.get("/vaga/")
	assert r0.status_code == 200 and r0.json() == []

	payload = {"titulo": "Dev", "descricao": "Descricao unica ABC", "carreira_id": car_id}
	r1 = client.post("/vaga/cadastro", json=payload)
	assert r1.status_code == 200
	body = r1.json()
	assert body.get("id") and body.get("titulo") == "Dev"
	assert body.get("carreira_id") == car_id


	r2 = client.get("/vaga/")
	assert r2.status_code == 200
	lista = r2.json()
	assert len(lista) == 1 and lista[0]["carreira_id"] == car_id
	assert isinstance(lista[0].get("carreira_nome"), (str, type(None)))

	r_dup = client.post("/vaga/cadastro", json=payload)
	assert r_dup.status_code == 409
	assert r_dup.json().get("detail") == "Já existe uma vaga com a mesma descrição."


def test_preview_habilidades_monkeypatched(app_client, monkeypatch):
	"""Simula extração/normalização e valida o preview de habilidades de uma vaga."""
	client, SessionLocal = app_client
	car_id = _criar_carreira(SessionLocal)
	cat_id = _criar_categoria(SessionLocal, "Backend")
	existing_hid = _criar_habilidade(SessionLocal, "Python", categoria_id=cat_id)
	from app.models import Habilidade, Categoria
	db = SessionLocal()
	try:
		existing_name = db.query(Habilidade.nome).filter(Habilidade.id == existing_hid).scalar()
		categoria_name = db.query(Categoria.nome).filter(Categoria.id == cat_id).scalar()
	finally:
		db.close()

	r_cad = client.post("/vaga/cadastro", json={
		"titulo": "Vaga P",
		"descricao": "qualquer descricao",
		"carreira_id": car_id,
	})
	vaga_id = r_cad.json()["id"]

	import app.services.extracao as extr

	def fake_extract(desc, session=None):
		"""Retorna habilidades simuladas usando nomes/categorias existentes do banco."""
		return [
			{"nome": existing_name, "categoria_sugerida": categoria_name},
			{"nome": "Flask", "categoria_sugerida": categoria_name},
		]

	def fake_norm(name, session=None):
		"""Normaliza o nome retornando-o inalterado (simulação)."""
		return name

	monkeypatch.setattr(extr, "extrair_habilidades_descricao", fake_extract)
	monkeypatch.setattr(extr, "normalizar_habilidade", fake_norm)
	# Patch também das referências importadas em app.services.vaga
	import app.services.vaga as vaga_srv
	monkeypatch.setattr(vaga_srv, "extrair_habilidades_descricao", fake_extract)
	monkeypatch.setattr(vaga_srv, "normalizar_habilidade", fake_norm)

	import app.services.vaga as vaga_srv
	monkeypatch.setattr(vaga_srv, "extrair_habilidades_descricao", fake_extract)
	monkeypatch.setattr(vaga_srv, "normalizar_habilidade", fake_norm)

	r = client.get(f"/vaga/{vaga_id}/preview-habilidades")
	assert r.status_code == 200
	itens = r.json()
	names = {i["nome"] for i in itens}
	assert any(n.startswith("Python") for n in names) and any(n.startswith("Flask") for n in names)
	python_it = next(i for i in itens if i["nome"] == existing_name)
	flask_it = next(i for i in itens if i["nome"].startswith("Flask"))
	assert python_it.get("habilidade_id") == existing_hid
	# Nova habilidade sugerida ainda não criada não tem habilidade_id
	assert flask_it.get("habilidade_id") in ("", None)
	assert flask_it.get("categoria_id") == cat_id


def test_confirmar_habilidades_cria_e_incrementa(app_client):
	"""Confirma habilidades de uma vaga: cria novas, identifica existentes e incrementa frequências."""
	client, SessionLocal = app_client
	car_id = _criar_carreira(SessionLocal)
	cat_id = _criar_categoria(SessionLocal, "Backend")
	existing_hid = _criar_habilidade(SessionLocal, "Python", categoria_id=cat_id)
	from app.models import Habilidade
	db = SessionLocal()
	try:
		existing_name = db.query(Habilidade.nome).filter(Habilidade.id == existing_hid).scalar()
	finally:
		db.close()

	r_cad = client.post("/vaga/cadastro", json={
		"titulo": "Vaga C",
		"descricao": "texto unico confirm",
		"carreira_id": car_id,
	})
	vaga_id = r_cad.json()["id"]

	payload = {
		"habilidades": [
			{"nome": existing_name},
			{"nome": "Flask", "categoria_sugerida": "Backend"},
		]
	}
	r = client.post(f"/vaga/{vaga_id}/confirmar-habilidades", json=payload)
	assert r.status_code == 200
	body = r.json()
	criados = body.get("habilidades_criadas", [])
	existiam = body.get("habilidades_ja_existiam", [])
	assert any(h.startswith("Flask") for h in criados)
	assert any(h == existing_name for h in existiam)

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
	"""Remove a relação vaga-habilidade e retorna 404 ao tentar remover novamente."""
	client, SessionLocal = app_client
	car_id = _criar_carreira(SessionLocal)
	cat_id = _criar_categoria(SessionLocal, "Backend")
	hid = _criar_habilidade(SessionLocal, "Django", categoria_id=cat_id)
	from app.models import Habilidade
	db = SessionLocal()
	try:
		django_name = db.query(Habilidade.nome).filter(Habilidade.id == hid).scalar()
	finally:
		db.close()

	r_cad = client.post("/vaga/cadastro", json={
		"titulo": "Vaga R",
		"descricao": "texto unico remover",
		"carreira_id": car_id,
	})
	vaga_id = r_cad.json()["id"]

	payload = {"habilidades": [{"nome": django_name}]}
	client.post(f"/vaga/{vaga_id}/confirmar-habilidades", json=payload)

	r = client.delete(f"/vaga/{vaga_id}/habilidades/{hid}")
	assert r.status_code == 200
	assert r.json().get("status") == "removido"

	r2 = client.delete(f"/vaga/{vaga_id}/habilidades/{hid}")
	assert r2.status_code == 404
	assert r2.json().get("detail") == "Relação não encontrada"


def test_excluir_vaga_decrementa_frequencias(app_client):
	"""Exclui uma vaga e verifica remoção das relações Carreira-Habilidade associadas."""
	client, SessionLocal = app_client
	car_id = _criar_carreira(SessionLocal)
	cat_id = _criar_categoria(SessionLocal, "Backend")
	hid1 = _criar_habilidade(SessionLocal, "Node.js", categoria_id=cat_id)
	hid2 = _criar_habilidade(SessionLocal, "React", categoria_id=cat_id)

	r_cad = client.post("/vaga/cadastro", json={
		"titulo": "Vaga D",
		"descricao": "texto unico deletar",
		"carreira_id": car_id,
	})
	vaga_id = r_cad.json()["id"]

	client.post(f"/vaga/{vaga_id}/confirmar-habilidades", json={
		"habilidades": [{"nome": "Node.js"}, {"nome": "React"}]
	})


	r = client.delete(f"/vaga/{vaga_id}")
	assert r.status_code == 200
	assert r.json().get("status") == "excluida"

	rel1 = _buscar_carreira_habilidade(SessionLocal, car_id, hid1)
	rel2 = _buscar_carreira_habilidade(SessionLocal, car_id, hid2)
	assert rel1 is None and rel2 is None

