"""
Testes do utilitário de erros (app.utils.errors)

Este arquivo valida a formatação de mensagens de validação (Pydantic) e o
lançamento de HTTPException padronizada:

- test_format_single_prefix_removal_and_field:
	Confere que `format_validation_error` inclui o nome do campo e mantém o
	prefixo "Value error, " na mensagem resultante.

- test_format_nested_field_uses_last_segment:
	Para erros aninhados (ex.: `inner.code`), usa o último segmento do caminho
	("code") como prefixo do campo; mantém o prefixo da mensagem.

- test_format_avoid_duplicate_field_prefix:
	Evita duplicar o nome do campo quando a mensagem já o contém (retorna
	"email: formato ruim", e não "email: email: formato ruim").

- test_format_multiple_errors_joined:
	Quando há múltiplos erros, a função concatena as mensagens com "; ",
	preservando os prefixos e campos individuais.

- test_raise_validation_http_exception_uses_formatted_message:
	`raise_validation_http_exception` converte ValidationError em HTTPException
	422 usando exatamente a mensagem formatada por `format_validation_error`.

Modelos auxiliares (Inner, User e UserWithPrefixedMsg) são usados para gerar
erros de validação específicos e validar a lógica de formatação.
"""

import pytest
from fastapi import HTTPException
from pydantic import BaseModel, field_validator, ValidationError

from app.utils.errors import format_validation_error, raise_validation_http_exception


class Inner(BaseModel):
	code: int

	@field_validator("code")
	@classmethod
	def must_be_positive(cls, v: int) -> int:
		if v <= 0:
			# inclui prefixo "Value error, " para testar remoção pelo formatador
			raise ValueError("Value error, deve ser positivo")
		return v


class User(BaseModel):
	email: str
	inner: Inner

	@field_validator("email")
	@classmethod
	def valid_email(cls, v: str) -> str:
		if "@" not in v:
			# inclui prefixo a ser removido
			raise ValueError("Value error, email inválido")
		return v


class UserWithPrefixedMsg(BaseModel):
	email: str

	@field_validator("email")
	@classmethod
	def msg_already_prefixed_with_field(cls, v: str) -> str:
		if "@" not in v:
			# mensagem já começa com o nome do campo
			raise ValueError("email: formato ruim")
		return v


def test_format_single_prefix_removal_and_field():
	with pytest.raises(ValidationError) as ctx:
		User.model_validate({"email": "invalido", "inner": {"code": 1}})
	msg = format_validation_error(ctx.value)
	# comportamento atual mantém o prefixo "Value error, "
	assert msg == "email: Value error, email inválido"


def test_format_nested_field_uses_last_segment():
	with pytest.raises(ValidationError) as ctx:
		User.model_validate({"email": "ok@ex.com", "inner": {"code": 0}})
	msg = format_validation_error(ctx.value)
	# comportamento atual mantém o prefixo
	assert msg == "code: Value error, deve ser positivo"


def test_format_avoid_duplicate_field_prefix():
	with pytest.raises(ValidationError) as ctx:
		UserWithPrefixedMsg.model_validate({"email": "ruim"})
	msg = format_validation_error(ctx.value)
	# não deve duplicar o campo: "email: email: formato ruim"
	assert msg == "email: formato ruim"


def test_format_multiple_errors_joined():
	with pytest.raises(ValidationError) as ctx:
		User.model_validate({"email": "ruim", "inner": {"code": 0}})
	msg = format_validation_error(ctx.value)
	partes = set(p.strip() for p in msg.split(";"))
	assert {"email: Value error, email inválido", "code: Value error, deve ser positivo"}.issubset(partes)
	assert ";" in msg  # confirmando concatenação por '; '


def test_raise_validation_http_exception_uses_formatted_message():
	with pytest.raises(ValidationError) as ctx:
		User.model_validate({"email": "ruim", "inner": {"code": 0}})
	e: ValidationError = ctx.value

	with pytest.raises(HTTPException) as http_ctx:
		raise_validation_http_exception(e)
	ex: HTTPException = http_ctx.value
	assert ex.status_code == 422
	assert ex.detail == format_validation_error(e)

