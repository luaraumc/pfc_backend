import pytest
from pydantic import ValidationError

from app.schemas.vagaSchemas import VagaBase, VagaOut
from tests.schemas.utils_test_schemas import make_obj


def test_vaga_base_valida_e_defaults():
	"""Valida criação de VagaBase com defaults e campos válidos."""
	m = VagaBase(titulo="Dev Jr", descricao="Desenvolvimento backend")
	assert m.titulo == "Dev Jr"
	assert m.descricao == "Desenvolvimento backend"
	assert m.carreira_id is None


def test_vaga_base_campos_obrigatorios():
	"""Garante obrigatoriedade de titulo e descricao em VagaBase."""
	with pytest.raises(ValidationError):
		VagaBase(descricao="Sem titulo")

	with pytest.raises(ValidationError):
		VagaBase(titulo="Sem descricao")


def test_vaga_base_coercao_tipos():
	"""Confere coerção de tipos: ints/strs e carreira_id str→int."""
	m = VagaBase(titulo=123, descricao=456, carreira_id="10")
	assert m.titulo == "123"
	assert m.descricao == "456"
	assert m.carreira_id == 10


def test_vaga_base_rejeita_none_em_obrigatorios_e_aceita_none_em_opcional():
	"""Rejeita None em campos obrigatórios e aceita None em carreira_id."""
	with pytest.raises(ValidationError):
		VagaBase(titulo=None, descricao="ok")

	with pytest.raises(ValidationError):
		VagaBase(titulo="ok", descricao=None)

	VagaBase(titulo="ok", descricao="ok", carreira_id=None)

def test_vaga_out_from_attributes_sucesso():
	"""Valida VagaOut via from_attributes com dados válidos."""
	obj = make_obj(id=1, titulo="Dev", descricao="Backend", carreira_id=2, carreira_nome="Engenharia")
	out = VagaOut.model_validate(obj)

	assert out.id == 1
	assert out.titulo == "Dev"
	assert out.descricao == "Backend"
	assert out.carreira_id == 2
	assert out.carreira_nome == "Engenharia"


def test_vaga_out_from_attributes_coercao_de_tipos():
	"""Confere coerção de tipos nos campos de VagaOut (str→int, int→str)."""
	obj = make_obj(id="7", titulo=111, descricao=222, carreira_id="3", carreira_nome=333)
	out = VagaOut.model_validate(obj)

	assert out.id == 7
	assert out.titulo == "111"
	assert out.descricao == "222"
	assert out.carreira_id == 3
	assert out.carreira_nome == "333"


def test_vaga_out_from_attributes_categoria_opcional():
	"""Garante que carreira_id e carreira_nome são opcionais em VagaOut."""
	obj = make_obj(id=1, titulo="Dev", descricao="Backend")
	out = VagaOut.model_validate(obj)

	assert out.carreira_id is None
	assert out.carreira_nome is None


def test_vaga_out_missing_id_erro():
	"""Dispara erro quando 'id' está ausente em VagaOut."""
	obj = make_obj(titulo="Dev", descricao="Backend")

	with pytest.raises(ValidationError):
		VagaOut.model_validate(obj)

