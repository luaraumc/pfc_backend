import pytest
from datetime import datetime
from pydantic import ValidationError
from tests.schemas.utils_test_schemas import make_obj


def test_carreira_base_criacao_valida_com_e_sem_descricao():
	"""Valida criação do CarreiraBase com e sem descrição."""
	from app.schemas.carreiraSchemas import CarreiraBase

	m1 = CarreiraBase(nome="Backend", descricao="APIs")
	assert m1.nome == "Backend" and m1.descricao == "APIs"

	m2 = CarreiraBase(nome="Data")
	assert m2.nome == "Data" and m2.descricao is None


@pytest.mark.parametrize("payload", [{"descricao": "X"}, {"nome": None}])
def test_carreira_base_requer_nome(payload):
	"""Garante que o campo nome é obrigatório no CarreiraBase."""
	from app.schemas.carreiraSchemas import CarreiraBase

	with pytest.raises(ValidationError):
		CarreiraBase(**payload)


def test_carreira_out_from_attributes():
	"""Valida CarreiraOut via from_attributes com campos esperados."""
	from app.schemas.carreiraSchemas import CarreiraOut

	d = make_obj(id=42, nome="Frontend", descricao="UI/UX", atualizado_em=datetime.utcnow())

	out = CarreiraOut.model_validate(d)
	assert out.id == 42
	assert out.nome == "Frontend"
	assert out.descricao == "UI/UX"
	assert isinstance(out.atualizado_em, datetime)

