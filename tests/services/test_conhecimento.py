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
from app.schemas import ConhecimentoBase, ConhecimentoOut
from app.services.conhecimento import (
	criar_conhecimento,
	listar_conhecimentos,
	buscar_conhecimento_por_id,
	atualizar_conhecimento,
	deletar_conhecimento,
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


def _payload(nome="Python") -> ConhecimentoBase:
	return ConhecimentoBase(nome=nome)


def test_listar_conhecimentos_vazio(session):
	itens = listar_conhecimentos(session)
	assert isinstance(itens, list)
	assert len(itens) == 0


def test_criar_conhecimento(session):
	payload = _payload("Python")
	out = criar_conhecimento(session, payload)
	assert isinstance(out, ConhecimentoOut)
	assert out.id is not None
	assert out.nome == "Python"


def test_listar_conhecimentos_populado(session):
	criar_conhecimento(session, _payload("Python"))
	criar_conhecimento(session, _payload("SQL"))
	itens = listar_conhecimentos(session)
	nomes = {i.nome for i in itens}
	assert len(itens) == 2
	assert {"Python", "SQL"}.issubset(nomes)


def test_buscar_conhecimento_por_id(session):
	out = criar_conhecimento(session, _payload("Docker"))
	achado = buscar_conhecimento_por_id(session, out.id)
	assert achado is not None
	assert achado.id == out.id
	assert achado.nome == "Docker"


def test_buscar_conhecimento_inexistente(session):
	assert buscar_conhecimento_por_id(session, 99999) is None


def test_atualizar_conhecimento(session):
	criado = criar_conhecimento(session, _payload("Git"))
	atualizado = atualizar_conhecimento(session, criado.id, ConhecimentoBase(nome="Git Avançado"))
	assert atualizado is not None
	assert atualizado.id == criado.id
	assert atualizado.nome == "Git Avançado"


def test_deletar_conhecimento(session):
	criado = criar_conhecimento(session, _payload("Kubernetes"))
	deletado = deletar_conhecimento(session, criado.id)
	assert deletado is not None
	assert deletado.id == criado.id
	assert buscar_conhecimento_por_id(session, criado.id) is None


def test_criar_conhecimento_duplicado_gera_integrity_error(session):
	criar_conhecimento(session, _payload("Java"))
	with pytest.raises(IntegrityError):
		criar_conhecimento(session, _payload("Java"))
	session.rollback()

