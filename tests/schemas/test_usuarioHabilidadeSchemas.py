import pytest
from pydantic import ValidationError

from app.schemas.usuarioHabilidadeSchemas import (
	UsuarioHabilidadeBase,
	UsuarioHabilidadeOut,
)
from .utils_test_schemas import make_obj


def test_usuario_habilidade_base_valido():
	"""Valida criação de UsuarioHabilidadeBase com IDs válidos."""
	m = UsuarioHabilidadeBase(usuario_id=1, habilidade_id=2)
	assert m.usuario_id == 1
	assert m.habilidade_id == 2


def test_usuario_habilidade_base_campos_obrigatorios():
	"""Garante que usuario_id e habilidade_id são obrigatórios."""
	with pytest.raises(ValidationError):
		UsuarioHabilidadeBase(habilidade_id=2)

	with pytest.raises(ValidationError):
		UsuarioHabilidadeBase(usuario_id=1)


def test_usuario_habilidade_base_coercao_strings_numericas():
	"""Confere coerção de strings numéricas para inteiros nos IDs."""
	m = UsuarioHabilidadeBase(usuario_id="10", habilidade_id="20")
	assert m.usuario_id == 10
	assert m.habilidade_id == 20


def test_usuario_habilidade_base_rejeita_strings_invalidas_e_none():
	"""Rejeita strings inválidas e None para IDs obrigatórios."""
	with pytest.raises(ValidationError):
		UsuarioHabilidadeBase(usuario_id="abc", habilidade_id=1)

	with pytest.raises(ValidationError):
		UsuarioHabilidadeBase(usuario_id=1, habilidade_id="xyz")

	with pytest.raises(ValidationError):
		UsuarioHabilidadeBase(usuario_id=None, habilidade_id=1)

	with pytest.raises(ValidationError):
		UsuarioHabilidadeBase(usuario_id=1, habilidade_id=None)


def test_usuario_habilidade_out_from_attributes_sucesso():
	"""Valida UsuarioHabilidadeOut via from_attributes com dados válidos."""
	obj = make_obj(id=1, usuario_id=2, habilidade_id=3)
	out = UsuarioHabilidadeOut.model_validate(obj)

	assert out.id == 1
	assert out.usuario_id == 2
	assert out.habilidade_id == 3


def test_usuario_habilidade_out_from_attributes_coercao_de_tipos():
	"""Confere coerção de tipos (str→int) em UsuarioHabilidadeOut."""
	obj = make_obj(id="7", usuario_id="8", habilidade_id="9")
	out = UsuarioHabilidadeOut.model_validate(obj)

	assert out.id == 7
	assert out.usuario_id == 8
	assert out.habilidade_id == 9


def test_usuario_habilidade_out_missing_campo_obrigatorio():
	"""Dispara erro quando faltar campo obrigatório em UsuarioHabilidadeOut."""
	obj_sem_id = make_obj(usuario_id=1, habilidade_id=2)

	with pytest.raises(ValidationError):
		UsuarioHabilidadeOut.model_validate(obj_sem_id)

	obj_sem_usuario = make_obj(id=1, habilidade_id=2)

	with pytest.raises(ValidationError):
		UsuarioHabilidadeOut.model_validate(obj_sem_usuario)

