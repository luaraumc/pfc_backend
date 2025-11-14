import pytest
from pydantic import ValidationError
from tests.schemas.utils_test_schemas import make_obj


def test_base_schema_construcao_valida():
	"""Valida construção correta do CarreiraHabilidadeBase com dados válidos."""
	from app.schemas.carreiraHabilidadeSchemas import CarreiraHabilidadeBase

	m = CarreiraHabilidadeBase(carreira_id=1, habilidade_id=2, frequencia=5)
	assert m.carreira_id == 1
	assert m.habilidade_id == 2
	assert m.frequencia == 5


@pytest.mark.parametrize(
	"payload",
	[
		{"habilidade_id": 2, "frequencia": 1},
		{"carreira_id": 1, "frequencia": 1},
		{"carreira_id": 1, "habilidade_id": 2},
	],
)
def test_base_schema_campos_obrigatorios(payload):
	"""Garante erro quando campos obrigatórios estão ausentes no base schema."""
	from app.schemas.carreiraHabilidadeSchemas import CarreiraHabilidadeBase

	with pytest.raises(ValidationError):
		CarreiraHabilidadeBase(**payload)


def test_base_schema_coerce_string_numerica_para_int():
	"""Confere coerção de strings numéricas para inteiros no base schema."""
	from app.schemas.carreiraHabilidadeSchemas import CarreiraHabilidadeBase

	m = CarreiraHabilidadeBase(carreira_id="1", habilidade_id="2", frequencia="3")
	assert m.carreira_id == 1 and m.habilidade_id == 2 and m.frequencia == 3


@pytest.mark.parametrize(
	"carreira_id,habilidade_id,frequencia",
	[("x", 2, 1), (1, "y", 1), (1, 2, "z")],
)
def test_base_schema_rejeita_strings_nao_numericas(carreira_id, habilidade_id, frequencia):
	"""Garante rejeição de strings não numéricas para IDs e frequência."""
	from app.schemas.carreiraHabilidadeSchemas import CarreiraHabilidadeBase

	with pytest.raises(ValidationError):
		CarreiraHabilidadeBase(
			carreira_id=carreira_id,
			habilidade_id=habilidade_id,
			frequencia=frequencia,
		)


def test_base_schema_nao_aceita_none_em_frequencia():
	"""Verifica que 'frequencia' não aceita None no base schema."""
	from app.schemas.carreiraHabilidadeSchemas import CarreiraHabilidadeBase

	with pytest.raises(ValidationError):
		CarreiraHabilidadeBase(carreira_id=1, habilidade_id=2, frequencia=None)


def test_out_schema_valida_id_e_from_attributes():
	"""Valida CarreiraHabilidadeOut via model_validate(from_attributes)."""
	from app.schemas.carreiraHabilidadeSchemas import CarreiraHabilidadeOut

	d = make_obj(id=10, carreira_id=1, habilidade_id=2, frequencia=7)

	out = CarreiraHabilidadeOut.model_validate(d)
	assert out.id == 10
	assert out.carreira_id == 1
	assert out.habilidade_id == 2
	assert out.frequencia == 7

