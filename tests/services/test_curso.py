import os
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
from app.schemas import CursoBase, CursoOut
from app.services.curso import (
	criar_curso,
	listar_cursos,
	buscar_curso_por_id,
	atualizar_curso,
	deletar_curso,
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


def _payload(nome="Curso A", descricao="Descricao A") -> CursoBase:
	return CursoBase(nome=nome, descricao=descricao)


def test_listar_cursos_vazio(session):
	itens = listar_cursos(session)
	assert isinstance(itens, list)
	assert len(itens) == 0


def test_criar_curso(session):
	payload = _payload("Python Básico", "Introdução a Python")
	out = criar_curso(session, payload)
	assert isinstance(out, CursoOut)
	assert out.id is not None
	assert out.nome == payload.nome
	assert out.descricao == payload.descricao


def test_listar_cursos_populado(session):
	criar_curso(session, _payload("Python", "Intro"))
	criar_curso(session, _payload("SQL", "Consultas"))
	itens = listar_cursos(session)
	nomes = {i.nome for i in itens}
	assert len(itens) == 2
	assert {"Python", "SQL"}.issubset(nomes)


def test_buscar_curso_por_id(session):
	criado = criar_curso(session, _payload("Docker", "Containers"))
	achado = buscar_curso_por_id(session, criado.id)
	assert achado is not None
	assert achado.id == criado.id
	assert achado.nome == "Docker"
	assert achado.descricao == "Containers"


def test_buscar_curso_inexistente(session):
	assert buscar_curso_por_id(session, 99999) is None


def test_atualizar_curso(session):
	criado = criar_curso(session, _payload("Git", "Controle de versão"))
	atualizado = atualizar_curso(session, criado.id, CursoBase(nome="Git Avançado", descricao="Fluxos e boas práticas"))
	assert atualizado is not None
	assert atualizado.id == criado.id
	assert atualizado.nome == "Git Avançado"
	assert atualizado.descricao == "Fluxos e boas práticas"


def test_deletar_curso(session):
	criado = criar_curso(session, _payload("Kubernetes", "Orquestração"))
	deletado = deletar_curso(session, criado.id)
	assert deletado is not None
	assert deletado.id == criado.id
	assert buscar_curso_por_id(session, criado.id) is None

