import os
import math
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Variáveis mínimas de ambiente para evitar erros nas imports
os.environ.setdefault("KEY_CRYPT", "test-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "testdb")

from app.dependencies import Base
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


@pytest.fixture(scope="function")
def session():
	engine = create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
	TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	Base.metadata.create_all(bind=engine)
	db = TestingSessionLocal()
	try:
		yield db
	finally:
		db.close()
		Base.metadata.drop_all(bind=engine)


# Helpers de criação
def cria_curso(session, nome: str, descricao: str = "Desc") -> Curso:
	c = Curso(nome=nome, descricao=descricao)
	session.add(c)
	session.commit()
	session.refresh(c)
	return c


def cria_carreira(session, nome: str, descricao: str = None) -> Carreira:
	car = Carreira(nome=nome, descricao=descricao)
	session.add(car)
	session.commit()
	session.refresh(car)
	return car


def cria_categoria(session, nome: str) -> Categoria:
	cat = Categoria(nome=nome)
	session.add(cat)
	session.commit()
	session.refresh(cat)
	return cat


def cria_conhecimento(session, nome: str) -> Conhecimento:
	k = Conhecimento(nome=nome)
	session.add(k)
	session.commit()
	session.refresh(k)
	return k


def vincula_curso_conhecimento(session, curso_id: int, conhecimento_id: int) -> CursoConhecimento:
	cc = CursoConhecimento(curso_id=curso_id, conhecimento_id=conhecimento_id)
	session.add(cc)
	session.commit()
	session.refresh(cc)
	return cc


def vincula_conhecimento_categoria(session, conhecimento_id: int, categoria_id: int, peso: int | None) -> ConhecimentoCategoria:
	kc = ConhecimentoCategoria(conhecimento_id=conhecimento_id, categoria_id=categoria_id, peso=peso)
	session.add(kc)
	session.commit()
	session.refresh(kc)
	return kc


def cria_habilidade(session, nome: str, categoria_id: int | None) -> Habilidade:
	h = Habilidade(nome=nome, categoria_id=categoria_id)
	session.add(h)
	session.commit()
	session.refresh(h)
	return h


def vincula_carreira_habilidade(session, carreira_id: int, habilidade_id: int, frequencia: int | None) -> CarreiraHabilidade:
	ch = CarreiraHabilidade(carreira_id=carreira_id, habilidade_id=habilidade_id, frequencia=frequencia)
	session.add(ch)
	session.commit()
	session.refresh(ch)
	return ch


# =========================
# Testes unitários
# =========================

def test_carregar_listas_base_ordenacao(session):
	c2 = cria_curso(session, "Zoologia")
	c1 = cria_curso(session, "Algoritmos")
	r2 = cria_carreira(session, "Segurança")
	r1 = cria_carreira(session, "Backend")

	cursos, carreiras = carregar_listas_base(session)
	assert [c["nome"] for c in cursos] == ["Algoritmos", "Zoologia"]
	assert [r["nome"] for r in carreiras] == ["Backend", "Segurança"]


def test_agregar_oferta_por_curso_soma_e_coalesce(session):
	# categorias
	cat_a = cria_categoria(session, "A")
	cat_b = cria_categoria(session, "B")
	# cursos e conhecimentos
	curso = cria_curso(session, "C1")
	k1 = cria_conhecimento(session, "K1")
	k2 = cria_conhecimento(session, "K2")
	vincula_curso_conhecimento(session, curso.id, k1.id)
	vincula_curso_conhecimento(session, curso.id, k2.id)
	# pesos: inclui None que vira 0; e 0 explícito
	vincula_conhecimento_categoria(session, k1.id, cat_a.id, peso=5)
	vincula_conhecimento_categoria(session, k2.id, cat_a.id, peso=None)
	vincula_conhecimento_categoria(session, k2.id, cat_b.id, peso=0)

	oferta = agregar_oferta_por_curso(session)
	assert oferta == {curso.id: {cat_a.id: 5.0, cat_b.id: 0.0}}


def test_agregar_demanda_por_carreira_soma(session):
	# categorias
	cat_a = cria_categoria(session, "A")
	# carreira e habilidades
	carreira = cria_carreira(session, "R1")
	h1 = cria_habilidade(session, "H1", categoria_id=cat_a.id)
	h2 = cria_habilidade(session, "H2", categoria_id=cat_a.id)
	vincula_carreira_habilidade(session, carreira.id, h1.id, frequencia=2)
	vincula_carreira_habilidade(session, carreira.id, h2.id, frequencia=None)  # None não soma

	demanda = agregar_demanda_por_carreira(session)
	assert demanda == {carreira.id: {cat_a.id: 2.0}}


def test_calcular_score_basico():
	oferta = {1: {10: 5.0, 11: 2.0}}
	demanda = {100: {10: 3.0, 11: 1.0}}
	s = calcular_score(oferta, demanda, curso_id=1, carreira_id=100)
	# (5*3 + 2*1) / (3+1) = 17/4 = 4.25
	assert math.isclose(s, 4.25, rel_tol=1e-9, abs_tol=1e-9)

	# denom zero => 0
	s2 = calcular_score(oferta, demanda, curso_id=2, carreira_id=999)
	assert s2 == 0.0


def test_montar_mapa_end_to_end(session):
	# categorias
	cat_a = cria_categoria(session, "A")
	cat_b = cria_categoria(session, "B")

	# cursos
	c1 = cria_curso(session, "Curso 1")
	c2 = cria_curso(session, "Curso 2")

	# conhecimentos e vínculos com cursos
	k1 = cria_conhecimento(session, "K1")
	k2 = cria_conhecimento(session, "K2")
	k3 = cria_conhecimento(session, "K3")
	vincula_curso_conhecimento(session, c1.id, k1.id)
	vincula_curso_conhecimento(session, c1.id, k2.id)
	vincula_curso_conhecimento(session, c2.id, k3.id)

	# pesos por categoria
	# curso 1: A=5 (K1->A), B=2 (K2->B)
	vincula_conhecimento_categoria(session, k1.id, cat_a.id, peso=5)
	vincula_conhecimento_categoria(session, k2.id, cat_b.id, peso=2)
	# curso 2: A=3 (K3->A)
	vincula_conhecimento_categoria(session, k3.id, cat_a.id, peso=3)

	# carreiras e habilidades
	r1 = cria_carreira(session, "Carreira X")
	r2 = cria_carreira(session, "Carreira Y")
	hA = cria_habilidade(session, "HA", categoria_id=cat_a.id)
	hB = cria_habilidade(session, "HB", categoria_id=cat_b.id)

	# demandas (frequências)
	# r1 demanda A:3, B:1
	vincula_carreira_habilidade(session, r1.id, hA.id, frequencia=3)
	vincula_carreira_habilidade(session, r1.id, hB.id, frequencia=1)
	# r2 demanda apenas A:2
	vincula_carreira_habilidade(session, r2.id, hA.id, frequencia=2)

	res = montar_mapa(session)

	# Cursos e carreiras ordenados por nome
	assert [c["nome"] for c in res["cursos"]] == ["Curso 1", "Curso 2"]
	assert [r["nome"] for r in res["carreiras"]] == ["Carreira X", "Carreira Y"]

	# Scores esperados:
	# c1 vs r1: oferta(A)=5, oferta(B)=2; demanda A=3, B=1 -> (5*3 + 2*1)/(3+1) = 17/4 = 4.25
	# c2 vs r1: oferta(A)=3; demanda A=3, B=1 -> (3*3 + 0*1)/4 = 9/4 = 2.25
	# c1 vs r2: (5*2)/2 = 5.0
	# c2 vs r2: (3*2)/2 = 3.0

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

