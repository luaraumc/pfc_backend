import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from tests.schemas.utils_test_schemas import senha_valida, invalid_emails


def test_login_schema_email_valido_e_sanitizado():
	"""Verifica que o LoginSchema sanitiza o e-mail e mantém a senha."""
	from app.schemas.authSchemas import LoginSchema

	data = LoginSchema(email="  user@example.com  ", senha="segura1")
	assert data.email == "user@example.com"
	assert data.senha == "segura1"


@pytest.mark.parametrize("email_invalido", invalid_emails())
def test_login_schema_email_invalido_dispara_erro(email_invalido):
	"""Garante que e-mails inválidos disparam ValidationError no LoginSchema."""
	from app.schemas.authSchemas import LoginSchema

	with pytest.raises(ValidationError) as exc:
		LoginSchema(email=email_invalido, senha="abcdef")
	assert "E-mail inválido" in str(exc.value)


@pytest.mark.parametrize("senha_invalida", ["abc", "abc 123", "\tabcdef", "abc\n123"])
def test_login_schema_senha_invalida_dispara_erro(senha_invalida):
	"""Garante que senhas inválidas disparam ValidationError no LoginSchema."""
	from app.schemas.authSchemas import LoginSchema

	with pytest.raises(ValidationError) as exc:
		LoginSchema(email="user@example.com", senha=senha_invalida)
	assert "Senha inválida" in str(exc.value)


def test_confirmar_nova_senha_valida():
	"""Valida que uma nova senha válida é aceita no schema."""
	from app.schemas.authSchemas import ConfirmarNovaSenhaSchema

	m = ConfirmarNovaSenhaSchema(email="a@a.com", codigo="123456", nova_senha=senha_valida())
	assert m.nova_senha == senha_valida()


@pytest.mark.parametrize(
	"senha,espera_msg",
	[
		("Abc!1", "Nova senha deve ter no mínimo 6 caracteres"),
		("Abc def!", "Nova senha não pode conter espaços"),
		("abcdef!", "Nova senha deve conter ao menos uma letra maiúscula"),
		("Abcdef1", "Nova senha deve conter ao menos um caractere especial"),
	],
)
def test_confirmar_nova_senha_invalida_dispara_erro(senha, espera_msg):
	"""Confere que mensagens corretas são retornadas para nova senha inválida."""
	from app.schemas.authSchemas import ConfirmarNovaSenhaSchema

	with pytest.raises(ValidationError) as exc:
		ConfirmarNovaSenhaSchema(email="a@a.com", codigo="123", nova_senha=senha)
	assert espera_msg in str(exc.value)


def test_instanciar_solicitar_confirmar_codigo_e_base():
	"""Smoke test: instancia e valida schemas de código e autenticação."""
	from app.schemas.authSchemas import (
		SolicitarCodigoSchema,
		ConfirmarCodigoSchema,
		CodigoAutenticacaoBase,
	)

	s = SolicitarCodigoSchema(email="user@example.com")
	assert s.email == "user@example.com"

	c = ConfirmarCodigoSchema(email="user@example.com", codigo="XYZ", motivo="recuperacao_senha")
	assert c.codigo == "XYZ" and c.motivo == "recuperacao_senha"

	base = CodigoAutenticacaoBase(
		usuario_id=1,
		codigo_recuperacao="ABC",
		codigo_expira_em=datetime.utcnow() + timedelta(hours=1),
		motivo="recuperacao_senha",
	)
	assert base.usuario_id == 1 and base.codigo_recuperacao == "ABC"

