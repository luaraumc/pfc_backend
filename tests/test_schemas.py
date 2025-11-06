"""
Testes do módulo app.schemas (modelos Pydantic e validadores)

Este arquivo verifica validações de entrada, defaults e serialização dos schemas:

- test_usuario_base_valid_ok_trims_email_and_defaults:
	Garante trim no e-mail e defaults em UsuarioBase (admin=False, carreira_id/curso_id=None).

- test_usuario_base_email_invalido (parametrizado):
	Valida mensagens de erro personalizadas para e-mails inválidos (sem "@" e sem ".com").

- test_usuario_base_senha_invalida (parametrizado):
	Verifica regras de senha (mín. 6 chars, ao menos 1 maiúscula e 1 caractere especial).

- test_login_schema_valid_e_erros:
	Confere caso válido e mensagens em e-mail inválido e senha curta no LoginSchema.

- test_confirmar_nova_senha_schema_erros (parametrizado):
	Checa mensagens de validação para a `nova_senha` (mesmas regras de complexidade).

- test_codigo_autenticacao_base_datetime_parse:
	Converte string ISO em datetime para `codigo_expira_em` em CodigoAutenticacaoBase.

- test_log_exclusao_base_defaults:
	Verifica defaults de LogExclusaoBase (acao, responsavel, motivo) e `data_hora_exclusao=None`.

- test_usuario_out_from_attributes:
	Monta UsuarioOut a partir de um objeto com atributos e valida tipos de datas.

- test_vaga_out_and_habilidade_out_from_attributes:
	Monta VagaOut e HabilidadeOut a partir de objetos simples e valida campos derivados
	(ex.: `carreira_nome` None e `categoria`="Backend").
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas import (
	UsuarioBase,
	UsuarioOut,
	LoginSchema,
	ConfirmarNovaSenhaSchema,
	LogExclusaoBase,
	CodigoAutenticacaoBase,
	VagaOut,
	HabilidadeOut,
)


def test_usuario_base_valid_ok_trims_email_and_defaults():
	m = UsuarioBase.model_validate({
		"nome": "Fulano",
		"email": "  fulano@empresa.com  ",
		"senha": "S3nh@Ok",
	})
	assert m.email == "fulano@empresa.com"
	assert m.admin is False
	assert m.carreira_id is None and m.curso_id is None


@pytest.mark.parametrize("email,erro", [
	("fulano", "E-mail inválido: deve conter '@'"),
	("fulano@empresa", "E-mail inválido: domínio deve conter '.com'"),
])
def test_usuario_base_email_invalido(email, erro):
	with pytest.raises(ValidationError) as ctx:
		UsuarioBase.model_validate({
			"nome": "X",
			"email": email,
			"senha": "S3nh@Ok",
		})
	msgs = [err.get("msg", "") for err in ctx.value.errors()]
	assert any(erro in m for m in msgs)


@pytest.mark.parametrize("senha,erro", [
	("Ab!", "Senha deve ter no mínimo 6 caracteres"),
	("abcdef!", "Senha deve conter ao menos uma letra maiúscula"),
	("Abcdef1", "Senha deve conter ao menos um caractere especial"),
])
def test_usuario_base_senha_invalida(senha, erro):
	with pytest.raises(ValidationError) as ctx:
		UsuarioBase.model_validate({
			"nome": "X",
			"email": "x@y.com",
			"senha": senha,
		})
	msgs = [err.get("msg", "") for err in ctx.value.errors()]
	assert any(erro in m for m in msgs)


def test_login_schema_valid_e_erros():
	ok = LoginSchema.model_validate({"email": "a@b.com", "senha": "123456"})
	assert ok.email == "a@b.com" and ok.senha == "123456"

	with pytest.raises(ValidationError) as e1:
		LoginSchema.model_validate({"email": "ruim", "senha": "123456"})
	msgs = [err.get("msg", "") for err in e1.value.errors()]
	assert any("E-mail inválido" in m for m in msgs)

	with pytest.raises(ValidationError) as e2:
		LoginSchema.model_validate({"email": "a@b.com", "senha": "123"})
	msgs2 = [err.get("msg", "") for err in e2.value.errors()]
	assert any("Senha inválida" in m for m in msgs2)


@pytest.mark.parametrize("senha,erro", [
	("Ab!", "Nova senha deve ter no mínimo 6 caracteres"),
	("abcdef!", "Nova senha deve conter ao menos uma letra maiúscula"),
	("Abcdef1", "Nova senha deve conter ao menos um caractere especial"),
])
def test_confirmar_nova_senha_schema_erros(senha, erro):
	with pytest.raises(ValidationError) as ctx:
		ConfirmarNovaSenhaSchema.model_validate({
			"email": "x@y.com",
			"codigo": "abc",
			"nova_senha": senha,
		})
	msgs = [err.get("msg", "") for err in ctx.value.errors()]
	assert any(erro in m for m in msgs)


def test_codigo_autenticacao_base_datetime_parse():
	m = CodigoAutenticacaoBase.model_validate({
		"usuario_id": 1,
		"codigo_recuperacao": "123",
		"codigo_expira_em": "2025-01-01T00:00:00",
		"motivo": "recuperacao_senha",
	})
	assert isinstance(m.codigo_expira_em, datetime)


def test_log_exclusao_base_defaults():
	m = LogExclusaoBase.model_validate({"email_hash": "h"})
	assert m.acao == "exclusao definitiva"
	assert m.responsavel == "usuario"
	assert m.motivo == "pedido do titular"
	assert m.data_hora_exclusao is None


def test_usuario_out_from_attributes():
	class U:
		def __init__(self):
			self.id = 1
			self.nome = "Fulano"
			self.email = "f@x.com"
			self.senha = "S3nh@Ok"
			self.admin = True
			self.carreira_id = None
			self.curso_id = None
			self.criado_em = datetime(2025, 1, 1, 0, 0, 0)
			self.atualizado_em = datetime(2025, 1, 1, 0, 1, 0)

	u = UsuarioOut.model_validate(U())
	assert u.id == 1 and u.nome == "Fulano" and u.admin is True
	assert isinstance(u.criado_em, datetime) and isinstance(u.atualizado_em, datetime)


def test_vaga_out_and_habilidade_out_from_attributes():
	class V:
		def __init__(self):
			self.id = 10
			self.titulo = "Dev"
			self.descricao = "desc"
			self.carreira_id = None
			self.carreira_nome = None

	class H:
		def __init__(self):
			self.id = 20
			self.nome = "Python"
			self.categoria_id = 1
			self.atualizado_em = datetime(2025, 1, 1)
			self.categoria = "Backend"

	v = VagaOut.model_validate(V())
	h = HabilidadeOut.model_validate(H())
	assert v.id == 10 and v.carreira_nome is None
	assert h.categoria == "Backend"
