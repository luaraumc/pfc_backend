import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

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
from app.models import Conhecimento, Categoria
from app.schemas import ConhecimentoCategoriaBase, ConhecimentoCategoriaOut
from app.services.conhecimentoCategoria import (
	criar_conhecimento_categoria,
	listar_conhecimento_categorias,
	remover_conhecimento_categoria,
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


# Helpers
def cria_conhecimento(session, nome="Python") -> Conhecimento:
	c = Conhecimento(nome=nome)
	session.add(c)
	session.commit()
	session.refresh(c)
	return c


def cria_categoria(session, nome="Tecnologia") -> Categoria:
	cat = Categoria(nome=nome)
	session.add(cat)
	session.commit()
	session.refresh(cat)
	return cat


def test_listar_conhecimento_categorias_vazio(session):
	conhecimento = cria_conhecimento(session, "Go")
	resultado = listar_conhecimento_categorias(session, conhecimento.id)
	assert isinstance(resultado, list)
	assert resultado == []


def test_criar_conhecimento_categoria(session):
	conhecimento = cria_conhecimento(session, "SQL")
	categoria = cria_categoria(session, "Banco de Dados")

	payload = ConhecimentoCategoriaBase(conhecimento_id=conhecimento.id, categoria_id=categoria.id, peso=5)
	out = criar_conhecimento_categoria(session, payload)

	assert isinstance(out, ConhecimentoCategoriaOut)
	assert out.id is not None
	assert out.conhecimento_id == conhecimento.id
	assert out.categoria_id == categoria.id
	assert out.peso == 5


def test_listar_conhecimento_categorias_populado(session):
	conhecimento = cria_conhecimento(session, "Cloud")
	cat1 = cria_categoria(session, "Infra")
	cat2 = cria_categoria(session, "DevOps")

	criar_conhecimento_categoria(session, ConhecimentoCategoriaBase(conhecimento_id=conhecimento.id, categoria_id=cat1.id, peso=3))
	criar_conhecimento_categoria(session, ConhecimentoCategoriaBase(conhecimento_id=conhecimento.id, categoria_id=cat2.id, peso=4))

	resultado = listar_conhecimento_categorias(session, conhecimento.id)
	assert len(resultado) == 2
	assert {cat1.id, cat2.id} == {r.categoria_id for r in resultado}


def test_remover_conhecimento_categoria(session):
	conhecimento = cria_conhecimento(session, "Segurança")
	cat = cria_categoria(session, "AppSec")
	criar_conhecimento_categoria(session, ConhecimentoCategoriaBase(conhecimento_id=conhecimento.id, categoria_id=cat.id, peso=2))

	removida = remover_conhecimento_categoria(session, conhecimento.id, cat.id)
	assert removida is not None
	assert removida.conhecimento_id == conhecimento.id
	assert removida.categoria_id == cat.id

	assert listar_conhecimento_categorias(session, conhecimento.id) == []


def test_remover_conhecimento_categoria_inexistente(session):
	conhecimento = cria_conhecimento(session, "Microserviços")
	assert remover_conhecimento_categoria(session, conhecimento.id, categoria_id=9999) is None


def test_criar_conhecimento_categoria_duplicada_gera_integrity_error(session):
	conhecimento = cria_conhecimento(session, "Frontend")
	cat = cria_categoria(session, "UI")

	criar_conhecimento_categoria(session, ConhecimentoCategoriaBase(conhecimento_id=conhecimento.id, categoria_id=cat.id, peso=1))

	with pytest.raises(IntegrityError):
		criar_conhecimento_categoria(session, ConhecimentoCategoriaBase(conhecimento_id=conhecimento.id, categoria_id=cat.id, peso=9))
	session.rollback()

