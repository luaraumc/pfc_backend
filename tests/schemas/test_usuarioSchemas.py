import pytest
from datetime import datetime
from pydantic import ValidationError
from tests.schemas.utils_test_schemas import (
	make_obj,
	senha_valida,
	invalid_emails,
	invalid_passwords_usuario,
)

from app.schemas.usuarioSchemas import (
	UsuarioBase,
	UsuarioOut,
	AtualizarUsuarioSchema,
)





def test_usuario_base_valido_defaults_e_opcionais():
	"""Valida defaults e campos opcionais ao criar UsuarioBase válido."""
	m = UsuarioBase(nome="Ana", email="ana@example.com", senha=senha_valida())
	assert m.admin is False
	assert m.carreira_id is None
	assert m.curso_id is None


def test_usuario_base_email_trim_e_formato_valido():
	"""Confere trim e formato válido para e-mail em UsuarioBase."""
	m = UsuarioBase(nome="Ana", email="  user@dominio.com  ", senha=senha_valida())
	assert m.email == "user@dominio.com"


@pytest.mark.parametrize("email", invalid_emails())
def test_usuario_base_email_invalido(email):
	"""Garante que e-mails inválidos disparam ValidationError em UsuarioBase."""
	with pytest.raises(ValidationError):
		UsuarioBase(nome="Ana", email=email, senha=senha_valida())


@pytest.mark.parametrize("senha", invalid_passwords_usuario())
def test_usuario_base_senha_invalida(senha):
	"""Garante que senhas inválidas disparam ValidationError em UsuarioBase."""
	with pytest.raises(ValidationError):
		UsuarioBase(nome="Ana", email="ana@example.com", senha=senha)


def test_usuario_base_coercao_ids_e_admin():
	"""Confere coerção de admin str→bool e IDs str→int em UsuarioBase."""
	m = UsuarioBase(
		nome="Bob",
		email="bob@example.com",
		senha=senha_valida(),
		admin="true",
		carreira_id="10",
		curso_id="20",
	)
	assert m.admin is True
	assert m.carreira_id == 10
	assert m.curso_id == 20


@pytest.mark.parametrize(
	"campo,valor",
	[
		("nome", None),
		("email", None),
		("senha", None),
	],
)
def test_usuario_base_rejeita_none_em_campos_obrigatorios(campo, valor):
	"""Rejeita None nos campos obrigatórios de UsuarioBase (nome, email, senha)."""
	dados = {"nome": "n", "email": "e@e.com", "senha": senha_valida()}
	dados[campo] = valor
	with pytest.raises(ValidationError):
		UsuarioBase(**dados)


class _DummyUsuario:
	pass


def test_usuario_out_from_attributes_sucesso_e_coercao():
	"""Valida UsuarioOut com coerção de tipos e datetimes válidos."""
	obj = make_obj(
		id="5",
		nome="Ana",
		email="ana@example.com",
		senha=senha_valida(),
		admin=True,
		carreira_id="7",
		curso_id="8",
		criado_em="2024-10-02T12:00:00",
		atualizado_em=datetime(2024, 10, 3, 9, 30, 0),
	)

	out = UsuarioOut.model_validate(obj)

	assert out.id == 5
	assert out.admin is True
	assert out.carreira_id == 7
	assert out.curso_id == 8
	assert isinstance(out.criado_em, datetime) and out.criado_em == datetime(2024, 10, 2, 12, 0, 0)
	assert isinstance(out.atualizado_em, datetime) and out.atualizado_em == datetime(2024, 10, 3, 9, 30, 0)


def test_usuario_out_herda_validacoes_email_e_senha():
	"""Garante que UsuarioOut mantém validações de e-mail/senha do base."""
	obj = make_obj(
		id=1,
		nome="Ana",
		email="usuario@dominio",
		senha=senha_valida(),
		admin=False,
		carreira_id=None,
		curso_id=None,
		criado_em=datetime(2024, 10, 2, 12, 0, 0),
		atualizado_em=datetime(2024, 10, 3, 9, 30, 0),
	)

	with pytest.raises(ValidationError):
		UsuarioOut.model_validate(obj)


def test_usuario_out_missing_campo_obrigatorio():
	"""Dispara erro quando faltar campo obrigatório em UsuarioOut (criado_em)."""
	obj = make_obj(
		id=1,
		nome="Ana",
		email="ana@example.com",
		senha=senha_valida(),
		admin=False,
		carreira_id=None,
		curso_id=None,
		atualizado_em=datetime(2024, 10, 3, 9, 30, 0),
	)

	with pytest.raises(ValidationError):
		UsuarioOut.model_validate(obj)


def test_atualizar_usuario_schema_valido_e_coercao():
	"""Valida AtualizarUsuarioSchema com coerção de IDs str→int."""
	m = AtualizarUsuarioSchema(nome="João", carreira_id="10", curso_id="11")
	assert m.nome == "João"
	assert m.carreira_id == 10
	assert m.curso_id == 11


@pytest.mark.parametrize("faltando", ["nome", "carreira_id", "curso_id"])
def test_atualizar_usuario_schema_campos_obrigatorios(faltando):
	"""Garante obrigatoriedade de nome, carreira_id e curso_id no update schema."""
	dados = {"nome": "n", "carreira_id": 1, "curso_id": 2}
	dados.pop(faltando)
	with pytest.raises(ValidationError):
		AtualizarUsuarioSchema(**dados)


def test_atualizar_usuario_schema_rejeita_none_obrigatorios():
	"""Rejeita None nos campos obrigatórios de AtualizarUsuarioSchema."""
	with pytest.raises(ValidationError):
		AtualizarUsuarioSchema(nome=None, carreira_id=1, curso_id=2)
	with pytest.raises(ValidationError):
		AtualizarUsuarioSchema(nome="n", carreira_id=None, curso_id=2)
	with pytest.raises(ValidationError):
		AtualizarUsuarioSchema(nome="n", carreira_id=1, curso_id=None)


def test_atualizar_usuario_schema_nome_int_coercao_para_str():
	"""Coerção de nome int→str em AtualizarUsuarioSchema."""
	m = AtualizarUsuarioSchema(nome=123, carreira_id=1, curso_id=2)
	assert m.nome == "123"

