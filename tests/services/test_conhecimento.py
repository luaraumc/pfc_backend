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

from app.schemas import ConhecimentoBase, ConhecimentoOut
from app.services.conhecimento import (
	criar_conhecimento,
	listar_conhecimentos,
	buscar_conhecimento_por_id,
	atualizar_conhecimento,
	deletar_conhecimento,
)
from tests.services.utils_test_services import session as session
from tests.services.utils_test_services import conhecimento_payload as _payload


def test_listar_conhecimentos_vazio(session):
	"""Garante lista vazia quando não há conhecimentos cadastrados."""
	itens = listar_conhecimentos(session)
	assert isinstance(itens, list)
	assert len(itens) == 0


def test_criar_conhecimento(session):
	"""Cria um conhecimento e valida o DTO retornado."""
	payload = _payload("Python")
	out = criar_conhecimento(session, payload)
	assert isinstance(out, ConhecimentoOut)
	assert out.id is not None
	assert out.nome == "Python"


def test_listar_conhecimentos_populado(session):
	"""Lista conhecimentos após inserir dois itens e confere nomes."""
	criar_conhecimento(session, _payload("Python"))
	criar_conhecimento(session, _payload("SQL"))
	itens = listar_conhecimentos(session)
	nomes = {i.nome for i in itens}
	assert len(itens) == 2
	assert {"Python", "SQL"}.issubset(nomes)


def test_buscar_conhecimento_por_id(session):
	"""Busca conhecimento por ID e valida o retorno."""
	out = criar_conhecimento(session, _payload("Docker"))
	achado = buscar_conhecimento_por_id(session, out.id)
	assert achado is not None
	assert achado.id == out.id
	assert achado.nome == "Docker"


def test_buscar_conhecimento_inexistente(session):
	"""Retorna None ao buscar conhecimento inexistente."""
	assert buscar_conhecimento_por_id(session, 99999) is None


def test_atualizar_conhecimento(session):
	"""Atualiza nome de um conhecimento existente."""
	criado = criar_conhecimento(session, _payload("Git"))
	atualizado = atualizar_conhecimento(session, criado.id, ConhecimentoBase(nome="Git Avançado"))
	assert atualizado is not None
	assert atualizado.id == criado.id
	assert atualizado.nome == "Git Avançado"


def test_deletar_conhecimento(session):
	"""Remove um conhecimento e confirma que não existe mais no banco."""
	criado = criar_conhecimento(session, _payload("Kubernetes"))
	deletado = deletar_conhecimento(session, criado.id)
	assert deletado is not None
	assert deletado.id == criado.id
	assert buscar_conhecimento_por_id(session, criado.id) is None


def test_criar_conhecimento_duplicado_gera_integrity_error(session):
	"""Criar conhecimento duplicado resulta em IntegrityError e rollback."""
	criar_conhecimento(session, _payload("Java"))
	with pytest.raises(IntegrityError):
		criar_conhecimento(session, _payload("Java"))
	session.rollback()

