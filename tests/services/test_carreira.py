import os
import pytest

os.environ.setdefault("KEY_CRYPT", "test-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "testdb")

from app.schemas import CarreiraOut, CarreiraBase
from app.services.carreira import (
	criar_carreira,
	listar_carreiras,
	buscar_carreira_por_id,
	atualizar_carreira,
	deletar_carreira,
)
from tests.services.utils_test_services import session as session
from tests.services.utils_test_services import carreira_payload as _cria_payload

def test_listar_carreiras_vazio(session):
	"""Garante lista vazia quando não há carreiras cadastradas."""
	carreiras = listar_carreiras(session)
	assert isinstance(carreiras, list)
	assert len(carreiras) == 0


def test_criar_carreira(session):
	"""Cria uma carreira e valida o retorno do DTO."""
	payload = _cria_payload()
	out = criar_carreira(session, payload)

	assert isinstance(out, CarreiraOut)
	assert out.id is not None
	assert out.nome == payload.nome
	assert out.descricao == payload.descricao


def test_listar_carreiras_populado(session):
	"""Lista carreiras após criar duas entradas e confere nomes."""
	criar_carreira(session, _cria_payload("Backend", "APIs"))
	criar_carreira(session, _cria_payload("Frontend", "UI/UX"))

	carreiras = listar_carreiras(session)
	nomes = {c.nome for c in carreiras}

	assert len(carreiras) == 2
	assert {"Backend", "Frontend"}.issubset(nomes)


def test_buscar_carreira_por_id(session):
	"""Busca uma carreira existente pelo ID e valida campos."""
	out = criar_carreira(session, _cria_payload("Dados", "ETL"))

	achada = buscar_carreira_por_id(session, out.id)
	assert achada is not None
	assert achada.id == out.id
	assert achada.nome == "Dados"
	assert achada.descricao == "ETL"


def test_buscar_carreira_inexistente(session):
	"""Retorna None ao buscar carreira inexistente."""
	assert buscar_carreira_por_id(session, 9999) is None


def test_atualizar_carreira(session):
	"""Atualiza parcialmente a carreira mantendo o nome e alterando descrição."""
	criada = criar_carreira(session, _cria_payload("Mobile", "Apps nativos"))
	atualizada = atualizar_carreira(session, criada.id, CarreiraBase(nome=criada.nome, descricao="Apps iOS/Android"))

	assert atualizada is not None
	assert atualizada.id == criada.id
	assert atualizada.nome == "Mobile"
	assert atualizada.descricao == "Apps iOS/Android"


def test_deletar_carreira(session):
	"""Deleta uma carreira e confirma que não pode mais ser encontrada."""
	criada = criar_carreira(session, _cria_payload("DevOps", "CI/CD"))

	deletada = deletar_carreira(session, criada.id)
	assert deletada is not None
	assert deletada.id == criada.id
	assert buscar_carreira_por_id(session, criada.id) is None

