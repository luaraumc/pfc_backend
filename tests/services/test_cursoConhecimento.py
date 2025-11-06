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
from app.models import Curso, Conhecimento
from app.schemas import CursoConhecimentoBase, CursoConhecimentoOut
from app.services.cursoConhecimento import (
	criar_curso_conhecimento,
	listar_curso_conhecimentos,
	remover_curso_conhecimento,
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
def cria_curso(session, nome="Curso X", descricao="Descricao do curso") -> Curso:
	c = Curso(nome=nome, descricao=descricao)
	session.add(c)
	session.commit()
	session.refresh(c)
	return c


def cria_conhecimento(session, nome="Python") -> Conhecimento:
	k = Conhecimento(nome=nome)
	session.add(k)
	session.commit()
	session.refresh(k)
	return k


def test_listar_curso_conhecimentos_vazio(session):
	curso = cria_curso(session, "Introdução a Dados", "ETL e conceitos")
	itens = listar_curso_conhecimentos(session, curso.id)
	assert isinstance(itens, list)
	assert itens == []


def test_criar_curso_conhecimento(session):
	curso = cria_curso(session, "Python Básico", "Linguagem e sintaxe")
	conhecimento = cria_conhecimento(session, "Python")

	payload = CursoConhecimentoBase(curso_id=curso.id, conhecimento_id=conhecimento.id)
	out = criar_curso_conhecimento(session, payload)

	assert isinstance(out, CursoConhecimentoOut)
	assert out.id is not None
	assert out.curso_id == curso.id
	assert out.conhecimento_id == conhecimento.id


def test_listar_curso_conhecimentos_populado(session):
	curso = cria_curso(session, "Banco de Dados", "SQL e modelagem")
	c1 = cria_conhecimento(session, "SQL")
	c2 = cria_conhecimento(session, "Modelagem")

	criar_curso_conhecimento(session, CursoConhecimentoBase(curso_id=curso.id, conhecimento_id=c1.id))
	criar_curso_conhecimento(session, CursoConhecimentoBase(curso_id=curso.id, conhecimento_id=c2.id))

	itens = listar_curso_conhecimentos(session, curso.id)
	assert len(itens) == 2
	assert {c1.id, c2.id} == {i.conhecimento_id for i in itens}


def test_remover_curso_conhecimento(session):
	curso = cria_curso(session, "DevOps", "CI/CD")
	c1 = cria_conhecimento(session, "Docker")
	criar_curso_conhecimento(session, CursoConhecimentoBase(curso_id=curso.id, conhecimento_id=c1.id))

	removido = remover_curso_conhecimento(session, curso.id, c1.id)
	assert removido is not None
	assert removido.curso_id == curso.id
	assert removido.conhecimento_id == c1.id

	assert listar_curso_conhecimentos(session, curso.id) == []


def test_remover_curso_conhecimento_inexistente(session):
	curso = cria_curso(session, "Redes", "TCP/IP")
	assert remover_curso_conhecimento(session, curso.id, conhecimento_id=9999) is None


def test_criar_curso_conhecimento_duplicado_gera_integrity_error(session):
	curso = cria_curso(session, "Web", "HTML/CSS/JS")
	c1 = cria_conhecimento(session, "HTML")

	criar_curso_conhecimento(session, CursoConhecimentoBase(curso_id=curso.id, conhecimento_id=c1.id))

	with pytest.raises(IntegrityError):
		criar_curso_conhecimento(session, CursoConhecimentoBase(curso_id=curso.id, conhecimento_id=c1.id))
	session.rollback()

