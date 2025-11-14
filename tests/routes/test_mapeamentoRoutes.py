import os
import sys

import pytest
from .utils_test_routes import app_client_context


@pytest.fixture(scope="module")
def app_client():
	"""Inicializa o TestClient padrão para rotas de mapeamento."""
	with app_client_context() as ctx:
		yield ctx


def _seed_basico(SessionLocal):
	"""Semeia cursos, carreiras, categorias, conhecimentos e relações básicas."""
	from app.models import Curso, Carreira, Categoria, Conhecimento, CursoConhecimento, ConhecimentoCategoria, Habilidade, CarreiraHabilidade
	db = SessionLocal()
	try:
		catA = Categoria(nome="CatA")
		catB = Categoria(nome="CatB")
		db.add_all([catA, catB])
		db.commit(); db.refresh(catA); db.refresh(catB)

		curso1 = Curso(nome="Curso1", descricao="d1")
		curso2 = Curso(nome="Curso2", descricao="d2")
		db.add_all([curso1, curso2]); db.commit(); db.refresh(curso1); db.refresh(curso2)

		car1 = Carreira(nome="Carreira1", descricao="x")
		car2 = Carreira(nome="Carreira2", descricao="y")
		db.add_all([car1, car2]); db.commit(); db.refresh(car1); db.refresh(car2)

		k1 = Conhecimento(nome="K1")
		k2 = Conhecimento(nome="K2")
		k3 = Conhecimento(nome="K3")
		db.add_all([k1, k2, k3]); db.commit(); db.refresh(k1); db.refresh(k2); db.refresh(k3)

		db.add_all([
			CursoConhecimento(curso_id=curso1.id, conhecimento_id=k1.id),
			CursoConhecimento(curso_id=curso1.id, conhecimento_id=k2.id),
			CursoConhecimento(curso_id=curso2.id, conhecimento_id=k3.id),
		])
		db.commit()

		db.add_all([
			ConhecimentoCategoria(conhecimento_id=k1.id, categoria_id=catA.id, peso=3),
			ConhecimentoCategoria(conhecimento_id=k2.id, categoria_id=catB.id, peso=1),
			ConhecimentoCategoria(conhecimento_id=k3.id, categoria_id=catA.id, peso=10),
		])
		db.commit()

		hA = Habilidade(nome="HA", categoria_id=catA.id)
		hB = Habilidade(nome="HB", categoria_id=catB.id)
		db.add_all([hA, hB]); db.commit(); db.refresh(hA); db.refresh(hB)

		db.add_all([
			CarreiraHabilidade(carreira_id=car1.id, habilidade_id=hA.id, frequencia=2),
			CarreiraHabilidade(carreira_id=car1.id, habilidade_id=hB.id, frequencia=1),
		])
		db.commit()

		return {
			"curso1_id": curso1.id,
			"curso2_id": curso2.id,
			"car1_id": car1.id,
			"car2_id": car2.id,
		}
	finally:
		db.close()


def test_mapa_vazio(app_client):
	"""Valida retorno do mapa vazio com listas e dicionários vazios."""
	client, _ = app_client
	r = client.get("/mapa/")
	assert r.status_code == 200
	data = r.json()
	for k in ("cursos", "carreiras", "cursoToCarreiras", "carreiraToCursos"):
		assert k in data
	assert data["cursos"] == [] and data["carreiras"] == []
	assert data["cursoToCarreiras"] == {} and data["carreiraToCursos"] == {}


def test_mapa_populado_scores_e_ordenacao(app_client):
	"""Verifica estrutura, cálculo de scores e ordenação das relações no mapa."""
	client, SessionLocal = app_client
	ids = _seed_basico(SessionLocal)

	r = client.get("/mapa/")
	assert r.status_code == 200
	body = r.json()

	cursos = body.get("cursos")
	carreiras = body.get("carreiras")
	c2k = body.get("cursoToCarreiras")
	k2c = body.get("carreiraToCursos")
	assert isinstance(cursos, list) and isinstance(carreiras, list)
	assert isinstance(c2k, dict) and isinstance(k2c, dict)

	curso_ids = {c["id"] for c in cursos}
	carreira_ids = {c["id"] for c in carreiras}
	assert ids["curso1_id"] in curso_ids and ids["curso2_id"] in curso_ids
	assert ids["car1_id"] in carreira_ids and ids["car2_id"] in carreira_ids

	s_c1 = next((x for x in c2k[str(ids["curso1_id"]) ] if x["id"] == ids["car1_id"]), None)
	s_c2 = next((x for x in c2k[str(ids["curso2_id"]) ] if x["id"] == ids["car1_id"]), None)
	assert s_c1 and s_c2
	assert abs(s_c1["score"] - 2.333333) < 1e-6
	assert abs(s_c2["score"] - 6.666667) < 1e-6

	assert c2k[str(ids["curso1_id"]) ] and c2k[str(ids["curso2_id"]) ]
	assert k2c[str(ids["car2_id"]) ] == []

	rels_car1 = k2c[str(ids["car1_id"]) ]
	assert [r["id"] for r in rels_car1] == [ids["curso2_id"], ids["curso1_id"]]

