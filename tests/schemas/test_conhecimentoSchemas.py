import pytest
from datetime import datetime
from pydantic import ValidationError
from tests.schemas.utils_test_schemas import make_obj


def test_conhecimento_base_criacao_valida():
	"""Valida criação do ConhecimentoBase com nome válido."""
	from app.schemas.conhecimentoSchemas import ConhecimentoBase

	m = ConhecimentoBase(nome="Estruturas de Dados")
	assert m.nome == "Estruturas de Dados"


@pytest.mark.parametrize("payload", [{}, {"nome": None}])
def test_conhecimento_base_requer_nome(payload):
	"""Garante que o campo nome é obrigatório no ConhecimentoBase."""
	from app.schemas.conhecimentoSchemas import ConhecimentoBase

	with pytest.raises(ValidationError):
		ConhecimentoBase(**payload)


def test_conhecimento_out_from_attributes():
	"""Valida ConhecimentoOut a partir de atributos válidos e datetime coerente."""
	from app.schemas.conhecimentoSchemas import ConhecimentoOut

	d = make_obj(id=11, nome="Algoritmos", atualizado_em=datetime.utcnow())

	out = ConhecimentoOut.model_validate(d)
	assert out.id == 11
	assert out.nome == "Algoritmos"
	assert isinstance(out.atualizado_em, datetime)

