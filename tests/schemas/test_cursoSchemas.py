import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.cursoSchemas import CursoBase, CursoOut
from tests.schemas.utils_test_schemas import make_obj


def test_curso_base_valido():
	"""Valida criação do CursoBase com nome e descrição válidos."""
	dado = {"nome": "Engenharia de Software", "descricao": "Curso focado em desenvolvimento."}
	modelo = CursoBase(**dado)

	assert modelo.nome == dado["nome"]
	assert modelo.descricao == dado["descricao"]


def test_curso_base_campo_nome_obrigatorio():
	"""Garante que nome é obrigatório em CursoBase."""
	with pytest.raises(ValidationError):
		CursoBase(descricao="Sem nome")


def test_curso_base_campo_descricao_obrigatorio():
	"""Garante que descricao é obrigatória em CursoBase."""
	with pytest.raises(ValidationError):
		CursoBase(nome="Sem descricao")


def test_curso_base_coercao_para_string_quando_numeros():
	"""Confere coerção de números para strings nos campos de CursoBase."""
	modelo = CursoBase(nome=123, descricao=456)

	assert isinstance(modelo.nome, str)
	assert isinstance(modelo.descricao, str)
	assert modelo.nome == "123"
	assert modelo.descricao == "456"


def test_curso_base_rejeita_none():
	"""Rejeita None em campos obrigatórios de CursoBase."""
	with pytest.raises(ValidationError):
		CursoBase(nome=None, descricao="ok")

	with pytest.raises(ValidationError):
		CursoBase(nome="ok", descricao=None)

    
def test_curso_out_from_attributes_sucesso():
	"""Valida CursoOut a partir de atributos válidos incluindo atualizado_em."""
	agora = datetime(2024, 10, 2, 12, 0, 0)
	obj = make_obj(id=1, nome="Curso X", descricao="Descricao X", atualizado_em=agora)

	out = CursoOut.model_validate(obj)

	assert out.id == 1
	assert out.nome == "Curso X"
	assert out.descricao == "Descricao X"
	assert out.atualizado_em == agora


def test_curso_out_from_attributes_com_coercao_de_tipos():
	"""Confere coerção de tipos: id str→int e datetime em ISO."""
	iso = "2024-10-02T12:00:00"
	obj = make_obj(id="10", nome="Curso Y", descricao="Descricao Y", atualizado_em=iso)

	out = CursoOut.model_validate(obj)

	assert out.id == 10
	assert isinstance(out.atualizado_em, datetime)


def test_curso_out_from_attributes_falta_campo_erro():
	"""Gera erro quando falta campo obrigatório em CursoOut (atualizado_em)."""
	obj = make_obj(id=1, nome="Nome", descricao="Desc")

	with pytest.raises(ValidationError):
		CursoOut.model_validate(obj)

