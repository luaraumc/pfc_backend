import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.habilidadeSchemas import (
	HabilidadeBase,
	HabilidadeOut,
	HabilidadeAtualizar,
)
from tests.schemas.utils_test_schemas import make_obj


def test_habilidade_base_valida():
	"""Valida criação do HabilidadeBase com nome válido."""
	dado = {"nome": "Comunicação"}
	modelo = HabilidadeBase(**dado)

	assert modelo.nome == "Comunicação"


def test_habilidade_base_nome_obrigatorio():
	"""Garante que nome é obrigatório no HabilidadeBase."""
	with pytest.raises(ValidationError):
		HabilidadeBase()


def test_habilidade_base_coercao_int_para_str():
	"""Confere coerção de int para str no campo nome."""
	modelo = HabilidadeBase(nome=123)
	assert isinstance(modelo.nome, str)
	assert modelo.nome == "123"


def test_habilidade_base_rejeita_none():
	"""Rejeita None no campo obrigatório nome do HabilidadeBase."""
	with pytest.raises(ValidationError):
		HabilidadeBase(nome=None)

def test_habilidade_out_from_attributes_sucesso():
	"""Valida HabilidadeOut com atributos completos e categoria presente."""
	agora = datetime(2024, 10, 2, 12, 0, 0)
	obj = make_obj(id=1, nome="Comunicação", categoria_id=5, atualizado_em=agora, categoria="Soft skill")

	out = HabilidadeOut.model_validate(obj)

	assert out.id == 1
	assert out.nome == "Comunicação"
	assert out.categoria_id == 5
	assert out.atualizado_em == agora
	assert out.categoria == "Soft skill"


def test_habilidade_out_from_attributes_coercao_de_tipos():
	"""Confere coerção de id/categoria_id str→int e ISO datetime."""
	iso = "2024-10-02T12:00:00"
	obj = make_obj(id="7", nome="Liderança", categoria_id="3", atualizado_em=iso)

	out = HabilidadeOut.model_validate(obj)

	assert out.id == 7
	assert out.categoria_id == 3
	assert isinstance(out.atualizado_em, datetime)
	assert out.categoria is None


def test_habilidade_out_from_attributes_categoria_opcional_quando_inexistente():
	"""Garante que 'categoria' é opcional quando não fornecida."""
	obj = make_obj(
		id=2,
		nome="Organização",
		categoria_id=9,
		atualizado_em=datetime(2024, 10, 3, 9, 30, 0),
	)

	out = HabilidadeOut.model_validate(obj)
	assert out.categoria is None


def test_habilidade_out_from_attributes_falta_campo_obrigatorio():
	"""Dispara erro quando faltar atualizado_em em HabilidadeOut."""
	obj = make_obj(id=1, nome="Pensamento Crítico", categoria_id=4)

	with pytest.raises(ValidationError):
		HabilidadeOut.model_validate(obj)

def test_habilidade_atualizar_totalmente_opcional():
	"""Valida que todos os campos de HabilidadeAtualizar são opcionais."""
	modelo = HabilidadeAtualizar()
	assert modelo.nome is None
	assert modelo.categoria_id is None


def test_habilidade_atualizar_parcial_por_nome():
	"""Permite atualização parcial apenas do nome."""
	modelo = HabilidadeAtualizar(nome="Negociação")
	assert modelo.nome == "Negociação"
	assert modelo.categoria_id is None


def test_habilidade_atualizar_parcial_por_categoria_id():
	"""Permite atualização parcial apenas do categoria_id."""
	modelo = HabilidadeAtualizar(categoria_id=8)
	assert modelo.nome is None
	assert modelo.categoria_id == 8


def test_habilidade_atualizar_coercao_categoria_id_str_para_int():
	"""Coerção de categoria_id de string numérica para inteiro."""
	modelo = HabilidadeAtualizar(categoria_id="12")
	assert isinstance(modelo.categoria_id, int)
	assert modelo.categoria_id == 12


def test_habilidade_atualizar_aceita_none_explicito():
	"""Aceita None explicitamente nos campos opcionais de atualização."""
	modelo = HabilidadeAtualizar(nome=None, categoria_id=None)
	assert modelo.nome is None
	assert modelo.categoria_id is None

