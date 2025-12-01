import os
import pytest
from sqlalchemy.exc import IntegrityError

os.environ.setdefault("KEY_CRYPT", "test-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "testdb")

from app.models import Curso, Conhecimento
from app.schemas import CursoConhecimentoBase, CursoConhecimentoOut
from app.services.cursoConhecimento import (
	criar_curso_conhecimento,
	listar_curso_conhecimentos,
	remover_curso_conhecimento,
)
from tests.services.utils_test_services import session as session
from tests.services.utils_test_services import (
    cria_curso,
    cria_conhecimento,
)


def test_listar_curso_conhecimentos_vazio(session):
	"""Retorna lista vazia de conhecimentos para curso novo."""
	curso = cria_curso(session, "Introdução a Dados", "ETL e conceitos")
	itens = listar_curso_conhecimentos(session, curso.id)
	assert isinstance(itens, list)
	assert itens == []


def test_criar_curso_conhecimento(session):
	"""Cria vínculo curso-conhecimento e valida DTO do retorno."""
	curso = cria_curso(session, "Python Básico", "Linguagem e sintaxe")
	conhecimento = cria_conhecimento(session, "Python")

	payload = CursoConhecimentoBase(curso_id=curso.id, conhecimento_id=conhecimento.id)
	out = criar_curso_conhecimento(session, payload)

	assert isinstance(out, CursoConhecimentoOut)
	assert out.id is not None
	assert out.curso_id == curso.id
	assert out.conhecimento_id == conhecimento.id


def test_listar_curso_conhecimentos_populado(session):
	"""Lista conhecimentos vinculados a um curso e confere IDs."""
	curso = cria_curso(session, "Banco de Dados", "SQL e modelagem")
	c1 = cria_conhecimento(session, "SQL")
	c2 = cria_conhecimento(session, "Modelagem")

	criar_curso_conhecimento(session, CursoConhecimentoBase(curso_id=curso.id, conhecimento_id=c1.id))
	criar_curso_conhecimento(session, CursoConhecimentoBase(curso_id=curso.id, conhecimento_id=c2.id))

	itens = listar_curso_conhecimentos(session, curso.id)
	assert len(itens) == 2
	assert {c1.id, c2.id} == {i.conhecimento_id for i in itens}


def test_remover_curso_conhecimento(session):
	"""Remove vínculo curso-conhecimento existente e valida remoção."""
	curso = cria_curso(session, "DevOps", "CI/CD")
	c1 = cria_conhecimento(session, "Docker")
	criar_curso_conhecimento(session, CursoConhecimentoBase(curso_id=curso.id, conhecimento_id=c1.id))

	removido = remover_curso_conhecimento(session, curso.id, c1.id)
	assert removido is not None
	assert removido.curso_id == curso.id
	assert removido.conhecimento_id == c1.id

	assert listar_curso_conhecimentos(session, curso.id) == []


def test_remover_curso_conhecimento_inexistente(session):
	"""Tenta remover vínculo inexistente e espera None."""
	curso = cria_curso(session, "Redes", "TCP/IP")
	assert remover_curso_conhecimento(session, curso.id, conhecimento_id=9999) is None


def test_criar_curso_conhecimento_duplicado_gera_integrity_error(session):
	"""Criar vínculo duplicado gera IntegrityError e mantém única linha."""
	curso = cria_curso(session, "Web", "HTML/CSS/JS")
	c1 = cria_conhecimento(session, "HTML")

	criar_curso_conhecimento(session, CursoConhecimentoBase(curso_id=curso.id, conhecimento_id=c1.id))

	with pytest.raises(IntegrityError):
		criar_curso_conhecimento(session, CursoConhecimentoBase(curso_id=curso.id, conhecimento_id=c1.id))
	session.rollback()

