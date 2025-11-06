import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Define variáveis de ambiente mínimas antes de importar módulos da app
os.environ.setdefault("KEY_CRYPT", "test-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
# Variáveis de banco exigidas por app.dependencies (não serão usadas nos testes)
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "testdb")

from app.dependencies import Base
from app.schemas import CarreiraBase, CarreiraOut
from app.services.carreira import (
	criar_carreira,
	listar_carreiras,
	buscar_carreira_por_id,
	atualizar_carreira,
	deletar_carreira,
)


# =========================
# Fixtures de banco (SQLite em memória)
# =========================

@pytest.fixture(scope="function")
def session():
	"""
	Cria uma sessão isolada em SQLite (memória) por teste.
	Usa o mesmo Base dos modelos do projeto.
	"""
	engine = create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
	TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

	# cria todas as tabelas necessárias para os modelos
	Base.metadata.create_all(bind=engine)

	db = TestingSessionLocal()
	try:
		yield db
	finally:
		db.close()
		Base.metadata.drop_all(bind=engine)


# =========================
# Helpers
# =========================

def _cria_payload(nome="Desenvolvedor(a) Backend", descricao="Atua com APIs e serviços") -> CarreiraBase:
	return CarreiraBase(nome=nome, descricao=descricao)


# =========================
# Testes CRUD - Carreira
# =========================

def test_listar_carreiras_vazio(session):
	carreiras = listar_carreiras(session)
	assert isinstance(carreiras, list)
	assert len(carreiras) == 0


def test_criar_carreira(session):
	payload = _cria_payload()
	out = criar_carreira(session, payload)

	assert isinstance(out, CarreiraOut)
	assert out.id is not None
	assert out.nome == payload.nome
	assert out.descricao == payload.descricao


def test_listar_carreiras_populado(session):
	criar_carreira(session, _cria_payload("Backend", "APIs"))
	criar_carreira(session, _cria_payload("Frontend", "UI/UX"))

	carreiras = listar_carreiras(session)
	nomes = {c.nome for c in carreiras}

	assert len(carreiras) == 2
	assert {"Backend", "Frontend"}.issubset(nomes)


def test_buscar_carreira_por_id(session):
	out = criar_carreira(session, _cria_payload("Dados", "ETL"))

	achada = buscar_carreira_por_id(session, out.id)
	assert achada is not None
	assert achada.id == out.id
	assert achada.nome == "Dados"
	assert achada.descricao == "ETL"


def test_buscar_carreira_inexistente(session):
	assert buscar_carreira_por_id(session, 9999) is None


def test_atualizar_carreira(session):
	criada = criar_carreira(session, _cria_payload("Mobile", "Apps nativos"))

	# Para atualizar parcialmente, CarreiraBase exige 'nome'; mantemos o mesmo e alteramos a descrição
	atualizada = atualizar_carreira(session, criada.id, CarreiraBase(nome=criada.nome, descricao="Apps iOS/Android"))

	assert atualizada is not None
	assert atualizada.id == criada.id
	assert atualizada.nome == "Mobile"
	assert atualizada.descricao == "Apps iOS/Android"


def test_deletar_carreira(session):
	criada = criar_carreira(session, _cria_payload("DevOps", "CI/CD"))

	deletada = deletar_carreira(session, criada.id)
	assert deletada is not None
	assert deletada.id == criada.id

	# Garante que foi removida
	assert buscar_carreira_por_id(session, criada.id) is None

