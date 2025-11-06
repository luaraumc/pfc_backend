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
	sys.modules.pop("app.main", None)
	sys.modules.pop("app.models", None)
	sys.modules.pop("app.dependencies", None)

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
	from app.dependencies import pegar_sessao

	# Override sessão
	def _override_session():
		db = TestingSessionLocal()
		try:
			yield db
		finally:
			db.close()

	app.dependency_overrides[pegar_sessao] = _override_session

	client = TestClient(app)

	try:
		yield client, TestingSessionLocal
	finally:
		app.dependency_overrides.clear()
		Base.metadata.drop_all(bind=engine)


def _seed_basico(SessionLocal):
	from app.models import Curso, Carreira, Categoria, Conhecimento, CursoConhecimento, ConhecimentoCategoria, Habilidade, CarreiraHabilidade
	db = SessionLocal()
	try:
		# Categorias
		catA = Categoria(nome="CatA")
		catB = Categoria(nome="CatB")
		db.add_all([catA, catB])
		db.commit(); db.refresh(catA); db.refresh(catB)

		# Cursos
		curso1 = Curso(nome="Curso1", descricao="d1")
		curso2 = Curso(nome="Curso2", descricao="d2")
		db.add_all([curso1, curso2]); db.commit(); db.refresh(curso1); db.refresh(curso2)

		# Carreiras
		car1 = Carreira(nome="Carreira1", descricao="x")
		car2 = Carreira(nome="Carreira2", descricao="y")
		db.add_all([car1, car2]); db.commit(); db.refresh(car1); db.refresh(car2)

		# Conhecimentos
		k1 = Conhecimento(nome="K1")
		k2 = Conhecimento(nome="K2")
		k3 = Conhecimento(nome="K3")
		db.add_all([k1, k2, k3]); db.commit(); db.refresh(k1); db.refresh(k2); db.refresh(k3)

		# CursoConhecimento
		db.add_all([
			CursoConhecimento(curso_id=curso1.id, conhecimento_id=k1.id),
			CursoConhecimento(curso_id=curso1.id, conhecimento_id=k2.id),
			CursoConhecimento(curso_id=curso2.id, conhecimento_id=k3.id),
		])
		db.commit()

		# ConhecimentoCategoria (pesos)
		db.add_all([
			ConhecimentoCategoria(conhecimento_id=k1.id, categoria_id=catA.id, peso=3),  # Curso1 → CatA += 3
			ConhecimentoCategoria(conhecimento_id=k2.id, categoria_id=catB.id, peso=1),  # Curso1 → CatB += 1
			ConhecimentoCategoria(conhecimento_id=k3.id, categoria_id=catA.id, peso=10), # Curso2 → CatA += 10
		])
		db.commit()

		# Habilidades (para demanda)
		hA = Habilidade(nome="HA", categoria_id=catA.id)
		hB = Habilidade(nome="HB", categoria_id=catB.id)
		db.add_all([hA, hB]); db.commit(); db.refresh(hA); db.refresh(hB)

		# CarreiraHabilidade (frequências)
		db.add_all([
			CarreiraHabilidade(carreira_id=car1.id, habilidade_id=hA.id, frequencia=2),
			CarreiraHabilidade(carreira_id=car1.id, habilidade_id=hB.id, frequencia=1),
			# car2 com frequência 0 (ou nenhuma relação) => score deve ser 0 e relações vazias
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
	client, _ = app_client
	r = client.get("/mapa/")
	assert r.status_code == 200
	data = r.json()
	for k in ("cursos", "carreiras", "cursoToCarreiras", "carreiraToCursos"):
		assert k in data
	assert data["cursos"] == [] and data["carreiras"] == []
	assert data["cursoToCarreiras"] == {} and data["carreiraToCursos"] == {}


def test_mapa_populado_scores_e_ordenacao(app_client):
	client, SessionLocal = app_client
	ids = _seed_basico(SessionLocal)

	r = client.get("/mapa/")
	assert r.status_code == 200
	body = r.json()

	# Estrutura básica
	cursos = body.get("cursos")
	carreiras = body.get("carreiras")
	c2k = body.get("cursoToCarreiras")
	k2c = body.get("carreiraToCursos")
	assert isinstance(cursos, list) and isinstance(carreiras, list)
	assert isinstance(c2k, dict) and isinstance(k2c, dict)

	# Cursos e carreiras presentes
	curso_ids = {c["id"] for c in cursos}
	carreira_ids = {c["id"] for c in carreiras}
	assert ids["curso1_id"] in curso_ids and ids["curso2_id"] in curso_ids
	assert ids["car1_id"] in carreira_ids and ids["car2_id"] in carreira_ids

	# Scores esperados:
	# curso1 vs car1: (CatA 3 * 2 + CatB 1 * 1) / (2 + 1) = 7/3 = 2.333333...
	# curso2 vs car1: (CatA 10 * 2 + CatB 0 * 1) / 3 = 20/3 = 6.666666...
	s_c1 = next((x for x in c2k[str(ids["curso1_id"]) ] if x["id"] == ids["car1_id"]), None)
	s_c2 = next((x for x in c2k[str(ids["curso2_id"]) ] if x["id"] == ids["car1_id"]), None)
	assert s_c1 and s_c2
	assert abs(s_c1["score"] - 2.333333) < 1e-6
	assert abs(s_c2["score"] - 6.666667) < 1e-6

	# car2 não deve ter relações (score 0 omitido)
	assert c2k[str(ids["curso1_id"]) ] and c2k[str(ids["curso2_id"]) ]
	assert k2c[str(ids["car2_id"]) ] == []

	# Ordem por score desc em carreiraToCursos[car1]
	rels_car1 = k2c[str(ids["car1_id"]) ]
	assert [r["id"] for r in rels_car1] == [ids["curso2_id"], ids["curso1_id"]]

