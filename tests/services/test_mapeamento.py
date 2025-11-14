import os
import math
import pytest

os.environ.setdefault("KEY_CRYPT", "test-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "testdb")

from app.models import (
	Curso,
	Carreira,
	Categoria,
	Conhecimento,
	CursoConhecimento,
	ConhecimentoCategoria,
	Habilidade,
	CarreiraHabilidade,
)
from app.services.mapeamento import (
	carregar_listas_base,
	agregar_oferta_por_curso,
	agregar_demanda_por_carreira,
	calcular_score,
	montar_mapa,
)
from tests.services.utils_test_services import session as session
from tests.services.utils_test_services import (
    cria_curso,
    cria_carreira,
    cria_categoria,
    cria_conhecimento,
    vincula_curso_conhecimento,
    vincula_conhecimento_categoria,
    cria_habilidade,
    vincula_carreira_habilidade,
)

def test_carregar_listas_base_ordenacao(session):
	"""Garante ordenação alfabética de cursos e carreiras carregados."""
	c2 = cria_curso(session, "Zoologia")
	c1 = cria_curso(session, "Algoritmos")
	r2 = cria_carreira(session, "Segurança")
	r1 = cria_carreira(session, "Backend")

	cursos, carreiras = carregar_listas_base(session)
	assert [c["nome"] for c in cursos] == ["Algoritmos", "Zoologia"]
	assert [r["nome"] for r in carreiras] == ["Backend", "Segurança"]


def test_agregar_oferta_por_curso_soma_e_coalesce(session):
	"""Soma pesos por categoria e trata valores None como 0 na oferta."""
	cat_a = cria_categoria(session, "A")
	cat_b = cria_categoria(session, "B")
	curso = cria_curso(session, "C1")
	k1 = cria_conhecimento(session, "K1")
	k2 = cria_conhecimento(session, "K2")
	vincula_curso_conhecimento(session, curso.id, k1.id)
	vincula_curso_conhecimento(session, curso.id, k2.id)
	vincula_conhecimento_categoria(session, k1.id, cat_a.id, peso=5)
	vincula_conhecimento_categoria(session, k2.id, cat_a.id, peso=None)
	vincula_conhecimento_categoria(session, k2.id, cat_b.id, peso=0)

	oferta = agregar_oferta_por_curso(session)
	assert oferta == {curso.id: {cat_a.id: 5.0, cat_b.id: 0.0}}


def test_agregar_demanda_por_carreira_soma(session):
	"""Agrega demanda somando frequências por categoria (ignora None)."""
	cat_a = cria_categoria(session, "A")
	carreira = cria_carreira(session, "R1")
	h1 = cria_habilidade(session, "H1", categoria_id=cat_a.id)
	h2 = cria_habilidade(session, "H2", categoria_id=cat_a.id)
	vincula_carreira_habilidade(session, carreira.id, h1.id, frequencia=2)
	vincula_carreira_habilidade(session, carreira.id, h2.id, frequencia=None)

	demanda = agregar_demanda_por_carreira(session)
	assert demanda == {carreira.id: {cat_a.id: 2.0}}


def test_calcular_score_basico():
	"""Calcula score ponderado oferta vs demanda e trata denominador zero."""
	oferta = {1: {10: 5.0, 11: 2.0}}
	demanda = {100: {10: 3.0, 11: 1.0}}
	s = calcular_score(oferta, demanda, curso_id=1, carreira_id=100)
	assert math.isclose(s, 4.25, rel_tol=1e-9, abs_tol=1e-9)
	s2 = calcular_score(oferta, demanda, curso_id=2, carreira_id=999)
	assert s2 == 0.0


def test_montar_mapa_end_to_end(session):
	"""Fluxo completo: monta mapa, ordena e valida scores esperados."""
	cat_a = cria_categoria(session, "A")
	cat_b = cria_categoria(session, "B")
	c1 = cria_curso(session, "Curso 1")
	c2 = cria_curso(session, "Curso 2")
	k1 = cria_conhecimento(session, "K1")
	k2 = cria_conhecimento(session, "K2")
	k3 = cria_conhecimento(session, "K3")
	vincula_curso_conhecimento(session, c1.id, k1.id)
	vincula_curso_conhecimento(session, c1.id, k2.id)
	vincula_curso_conhecimento(session, c2.id, k3.id)
	vincula_conhecimento_categoria(session, k1.id, cat_a.id, peso=5)
	vincula_conhecimento_categoria(session, k2.id, cat_b.id, peso=2)
	vincula_conhecimento_categoria(session, k3.id, cat_a.id, peso=3)
	r1 = cria_carreira(session, "Carreira X")
	r2 = cria_carreira(session, "Carreira Y")
	hA = cria_habilidade(session, "HA", categoria_id=cat_a.id)
	hB = cria_habilidade(session, "HB", categoria_id=cat_b.id)
	vincula_carreira_habilidade(session, r1.id, hA.id, frequencia=3)
	vincula_carreira_habilidade(session, r1.id, hB.id, frequencia=1)
	vincula_carreira_habilidade(session, r2.id, hA.id, frequencia=2)

	res = montar_mapa(session)
	assert [c["nome"] for c in res["cursos"]] == ["Curso 1", "Curso 2"]
	assert [r["nome"] for r in res["carreiras"]] == ["Carreira X", "Carreira Y"]

	c1_list = res["cursoToCarreiras"][c1.id]
	assert [x["nome"] for x in c1_list] == ["Carreira Y", "Carreira X"]
	assert [x["score"] for x in c1_list] == [5.0, 4.25]

	c2_list = res["cursoToCarreiras"][c2.id]
	assert [x["nome"] for x in c2_list] == ["Carreira Y", "Carreira X"]
	assert [x["score"] for x in c2_list] == [3.0, 2.25]

	r1_list = res["carreiraToCursos"][r1.id]
	assert [x["nome"] for x in r1_list] == ["Curso 1", "Curso 2"]
	assert [x["score"] for x in r1_list] == [4.25, 2.25]

	r2_list = res["carreiraToCursos"][r2.id]
	assert [x["nome"] for x in r2_list] == ["Curso 1", "Curso 2"]
	assert [x["score"] for x in r2_list] == [5.0, 3.0]

