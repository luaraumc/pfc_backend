import pytest
from pydantic import ValidationError
from tests.schemas.utils_test_schemas import make_obj


def test_base_construcao_valida_sem_peso_e_com_limites():
	"""Valida construção com peso None e nos limites 0 e 3."""
	from app.schemas.conhecimentoCategoriaSchemas import ConhecimentoCategoriaBase

	m1 = ConhecimentoCategoriaBase(conhecimento_id=1, categoria_id=2, peso=None)
	assert m1.peso is None

	m2 = ConhecimentoCategoriaBase(conhecimento_id=1, categoria_id=2, peso=0)
	m3 = ConhecimentoCategoriaBase(conhecimento_id=1, categoria_id=2, peso=3)
	assert m2.peso == 0 and m3.peso == 3


@pytest.mark.parametrize("peso_invalido", [-1, 4])
def test_base_peso_fora_intervalo_dispara_erro(peso_invalido):
	"""Garante erro quando o peso está fora do intervalo permitido (0-3)."""
	from app.schemas.conhecimentoCategoriaSchemas import ConhecimentoCategoriaBase

	with pytest.raises(ValidationError) as exc:
		ConhecimentoCategoriaBase(conhecimento_id=1, categoria_id=2, peso=peso_invalido)
	assert "peso deve estar entre 0 e 3" in str(exc.value)


def test_base_coerce_string_numerica_para_int():
	"""Confere coerção de strings numéricas para inteiros nos campos IDs e peso."""
	from app.schemas.conhecimentoCategoriaSchemas import ConhecimentoCategoriaBase

	m = ConhecimentoCategoriaBase(conhecimento_id="1", categoria_id="2", peso="3")
	assert m.conhecimento_id == 1 and m.categoria_id == 2 and m.peso == 3


@pytest.mark.parametrize(
	"conhecimento_id,categoria_id,peso",
	[("x", 2, 1), (1, "y", 1), (1, 2, "z")],
)
def test_base_rejeita_strings_nao_numericas(conhecimento_id, categoria_id, peso):
	"""Rejeita valores não numéricos para IDs e peso no base schema."""
	from app.schemas.conhecimentoCategoriaSchemas import ConhecimentoCategoriaBase

	with pytest.raises(ValidationError):
		ConhecimentoCategoriaBase(conhecimento_id=conhecimento_id, categoria_id=categoria_id, peso=peso)


def test_out_from_attributes():
	"""Valida ConhecimentoCategoriaOut via from_attributes com dados válidos."""
	from app.schemas.conhecimentoCategoriaSchemas import ConhecimentoCategoriaOut

	d = make_obj(id=10, conhecimento_id=1, categoria_id=2, peso=2)

	out = ConhecimentoCategoriaOut.model_validate(d)
	assert out.id == 10
	assert out.conhecimento_id == 1
	assert out.categoria_id == 2
	assert out.peso == 2


def test_atualizar_aceita_parciais_e_none():
	"""Confere que atualização aceita parciais e valores None sem erro."""
	from app.schemas.conhecimentoCategoriaSchemas import ConhecimentoCategoriaAtualizar

	m1 = ConhecimentoCategoriaAtualizar(categoria_id=3)
	assert m1.categoria_id == 3 and m1.peso is None

	m2 = ConhecimentoCategoriaAtualizar(peso=0)
	assert m2.peso == 0 and m2.categoria_id is None

	m3 = ConhecimentoCategoriaAtualizar(categoria_id=None, peso=None)
	assert m3.categoria_id is None and m3.peso is None


@pytest.mark.parametrize("peso_invalido", [-1, 4])
def test_atualizar_peso_fora_intervalo_dispara_erro(peso_invalido):
	"""Garante erro ao atualizar com peso fora do intervalo (0-3)."""
	from app.schemas.conhecimentoCategoriaSchemas import ConhecimentoCategoriaAtualizar

	with pytest.raises(ValidationError) as exc:
		ConhecimentoCategoriaAtualizar(peso=peso_invalido)
	assert "peso deve estar entre 0 e 3" in str(exc.value)

