import pytest
from pydantic import ValidationError
from tests.schemas.utils_test_schemas import make_obj


def test_curso_conhecimento_base_construcao_valida():
	"""Valida criação do CursoConhecimentoBase com IDs válidos."""
	from app.schemas.cursoConhecimentoSchemas import CursoConhecimentoBase

	m = CursoConhecimentoBase(curso_id=1, conhecimento_id=2)
	assert m.curso_id == 1 and m.conhecimento_id == 2


@pytest.mark.parametrize(
	"payload",
	[
		{"conhecimento_id": 2},
		{"curso_id": 1},
		{},
	],
)
def test_curso_conhecimento_base_campos_obrigatorios(payload):
    """Garante erro quando campos obrigatórios estão ausentes no base schema."""
	from app.schemas.cursoConhecimentoSchemas import CursoConhecimentoBase

	with pytest.raises(ValidationError):
		CursoConhecimentoBase(**payload)


def test_curso_conhecimento_base_coerce_strings_numericas():
	"""Confere coerção de strings numéricas para inteiros nos IDs."""
	from app.schemas.cursoConhecimentoSchemas import CursoConhecimentoBase

	m = CursoConhecimentoBase(curso_id="1", conhecimento_id="2")
	assert m.curso_id == 1 and m.conhecimento_id == 2


@pytest.mark.parametrize(
	"curso_id,conhecimento_id",
	[("x", 2), (1, "y"), ("a", "b")],
)
def test_curso_conhecimento_base_rejeita_strings_invalidas(curso_id, conhecimento_id):
	"""Rejeita strings não numéricas passadas como IDs no base schema."""
	from app.schemas.cursoConhecimentoSchemas import CursoConhecimentoBase

	with pytest.raises(ValidationError):
		CursoConhecimentoBase(curso_id=curso_id, conhecimento_id=conhecimento_id)


def test_curso_conhecimento_out_from_attributes():
	"""Valida CursoConhecimentoOut via from_attributes com dados válidos."""
	from app.schemas.cursoConhecimentoSchemas import CursoConhecimentoOut

	d = make_obj(id=5, curso_id=1, conhecimento_id=2)

	out = CursoConhecimentoOut.model_validate(d)
	assert out.id == 5
	assert out.curso_id == 1
	assert out.conhecimento_id == 2

