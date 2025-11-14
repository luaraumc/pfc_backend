import pytest
from datetime import datetime
from pydantic import ValidationError
from tests.schemas.utils_test_schemas import make_obj


def test_categoria_base_criacao_valida():
	"""Valida criação do CategoriaBase com nome válido."""
	from app.schemas.categoriaSchemas import CategoriaBase

	m = CategoriaBase(nome="Backend")
	assert m.nome == "Backend"


@pytest.mark.parametrize("payload", [{}, {"nome": None}])
def test_categoria_base_requer_nome(payload):
	"""Garante que o campo nome é obrigatório no CategoriaBase."""
	from app.schemas.categoriaSchemas import CategoriaBase

	with pytest.raises(ValidationError):
		CategoriaBase(**payload)


def test_categoria_out_from_attributes():
	"""Valida CategoriaOut construído a partir de atributos válidos."""
	from app.schemas.categoriaSchemas import CategoriaOut

	d = make_obj(id=7, nome="Dados", atualizado_em=datetime.utcnow())

	out = CategoriaOut.model_validate(d)
	assert out.id == 7
	assert out.nome == "Dados"
	assert isinstance(out.atualizado_em, datetime)

