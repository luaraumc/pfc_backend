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

from app.models import Carreira, Habilidade, Categoria
from app.schemas import CarreiraHabilidadeBase, CarreiraHabilidadeOut
from app.services.carreiraHabilidade import (
	criar_carreira_habilidade,
	listar_carreira_habilidades,
	remover_carreira_habilidade,
)
from tests.services.utils_test_services import session as session
from tests.services.utils_test_services import (
    cria_categoria,
    cria_carreira,
    cria_habilidade,
)

def test_listar_carreira_habilidades_vazio(session):
	"""Lista relacionamentos vazios de carreira-habilidade para nova carreira."""
	carreira = cria_carreira(session)
	resultado = listar_carreira_habilidades(session, carreira.id)
	assert isinstance(resultado, list)
	assert len(resultado) == 0


def test_criar_carreira_habilidade(session):
	"""Cria vínculo carreira-habilidade com frequência e valida retorno."""
	cat = cria_categoria(session)
	carreira = cria_carreira(session)
	habilidade = cria_habilidade(session, nome="Python", categoria_id=cat.id)

	payload = CarreiraHabilidadeBase(
		carreira_id=carreira.id,
		habilidade_id=habilidade.id,
		frequencia=7,
	)
	out = criar_carreira_habilidade(session, payload)

	assert isinstance(out, CarreiraHabilidadeOut)
	assert out.id is not None
	assert out.carreira_id == carreira.id
	assert out.habilidade_id == habilidade.id
	assert out.frequencia == 7


def test_listar_carreira_habilidades_populado(session):
	"""Lista dois vínculos criados e confere suas habilidades associadas."""
	cat = cria_categoria(session)
	carreira = cria_carreira(session)
	hab1 = cria_habilidade(session, nome="Python", categoria_id=cat.id)
	hab2 = cria_habilidade(session, nome="SQL", categoria_id=cat.id)

	criar_carreira_habilidade(session, CarreiraHabilidadeBase(carreira_id=carreira.id, habilidade_id=hab1.id, frequencia=3))
	criar_carreira_habilidade(session, CarreiraHabilidadeBase(carreira_id=carreira.id, habilidade_id=hab2.id, frequencia=5))

	resultado = listar_carreira_habilidades(session, carreira.id)
	assert len(resultado) == 2
	assert {hab1.id, hab2.id} == {r.habilidade_id for r in resultado}


def test_remover_carreira_habilidade(session):
	"""Remove vínculo existente de carreira-habilidade e valida remoção."""
	cat = cria_categoria(session)
	carreira = cria_carreira(session)
	hab = cria_habilidade(session, nome="Docker", categoria_id=cat.id)
	criar_carreira_habilidade(session, CarreiraHabilidadeBase(carreira_id=carreira.id, habilidade_id=hab.id, frequencia=1))

	removida = remover_carreira_habilidade(session, carreira.id, hab.id)
	assert removida is not None
	assert removida.carreira_id == carreira.id
	assert removida.habilidade_id == hab.id
	assert listar_carreira_habilidades(session, carreira.id) == []


def test_remover_carreira_habilidade_inexistente(session):
	"""Tenta remover vínculo inexistente e deve retornar None."""
	carreira = cria_carreira(session)
	assert remover_carreira_habilidade(session, carreira.id, habilidade_id=9999) is None


def test_criar_carreira_habilidade_duplicada_gera_integrity_error(session):
	"""Criar vínculo duplicado dispara IntegrityError e mantém único registro."""
	cat = cria_categoria(session)
	carreira = cria_carreira(session)
	hab = cria_habilidade(session, nome="Git", categoria_id=cat.id)

	criar_carreira_habilidade(session, CarreiraHabilidadeBase(carreira_id=carreira.id, habilidade_id=hab.id, frequencia=2))

	with pytest.raises(IntegrityError):
		criar_carreira_habilidade(session, CarreiraHabilidadeBase(carreira_id=carreira.id, habilidade_id=hab.id, frequencia=9))
	session.rollback()

	resultado = listar_carreira_habilidades(session, carreira.id)
	assert len(resultado) == 1
