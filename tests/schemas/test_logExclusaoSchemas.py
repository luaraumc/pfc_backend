import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.logExclusaoSchemas import LogExclusaoBase, LogExclusaoOut
from tests.schemas.utils_test_schemas import make_obj


def test_log_exclusao_base_minimo_com_defaults():
	"""Valida defaults e campos mínimos em LogExclusaoBase."""
	m = LogExclusaoBase(email_hash="abc123")

	assert m.email_hash == "abc123"
	assert m.acao == "exclusao definitiva"
	assert m.responsavel == "usuario"
	assert m.motivo == "pedido do titular"
	assert m.data_hora_exclusao is None


def test_log_exclusao_base_coercao_para_string():
	"""Confere coerção para string nos campos textuais do base schema."""
	m = LogExclusaoBase(email_hash=123, acao=1, responsavel=2, motivo=3)

	assert m.email_hash == "123"
	assert m.acao == "1"
	assert m.responsavel == "2"
	assert m.motivo == "3"


def test_log_exclusao_base_parse_datetime_iso():
	"""Valida parsing de datetime em formato ISO no base schema."""
	iso = "2024-10-02T12:00:00"
	m = LogExclusaoBase(email_hash="h", data_hora_exclusao=iso)
	assert isinstance(m.data_hora_exclusao, datetime)
	assert m.data_hora_exclusao == datetime(2024, 10, 2, 12, 0, 0)


def test_log_exclusao_base_email_hash_obrigatorio_e_rejeita_none():
	"""Garante obrigatoriedade de email_hash e rejeição de None."""
	with pytest.raises(ValidationError):
		LogExclusaoBase()

	with pytest.raises(ValidationError):
		LogExclusaoBase(email_hash=None)


def test_log_exclusao_base_rejeita_none_em_campos_texto():
	"""Rejeita None nos campos textuais do base schema."""
	with pytest.raises(ValidationError):
		LogExclusaoBase(email_hash="x", acao=None)

	with pytest.raises(ValidationError):
		LogExclusaoBase(email_hash="x", responsavel=None)

	with pytest.raises(ValidationError):
		LogExclusaoBase(email_hash="x", motivo=None)



def test_log_exclusao_out_from_attributes_sucesso():
	"""Valida LogExclusaoOut com todos os atributos válidos."""
	agora = datetime(2024, 10, 2, 12, 0, 0)
	obj = make_obj(
		id=1,
		email_hash="e1",
		acao="exclusao definitiva",
		data_hora_exclusao=agora,
		responsavel="usuario",
		motivo="pedido do titular",
	)

	out = LogExclusaoOut.model_validate(obj)

	assert out.id == 1
	assert out.email_hash == "e1"
	assert out.acao == "exclusao definitiva"
	assert out.data_hora_exclusao == agora
	assert out.responsavel == "usuario"
	assert out.motivo == "pedido do titular"


def test_log_exclusao_out_from_attributes_coercao_de_tipos():
	"""Confere coerção de tipos: id str→int e ISO datetime."""
	iso = "2024-10-02T12:00:00"
	obj = make_obj(
		id="10",
		email_hash=999,
		acao=1,
		data_hora_exclusao=iso,
		responsavel=2,
		motivo=3,
	)

	out = LogExclusaoOut.model_validate(obj)

	assert out.id == 10
	assert out.email_hash == "999"
	assert out.acao == "1"
	assert isinstance(out.data_hora_exclusao, datetime)
	assert out.responsavel == "2"
	assert out.motivo == "3"


def test_log_exclusao_out_missing_id_erro():
	"""Dispara erro quando 'id' está ausente em LogExclusaoOut."""
	obj = make_obj(
		email_hash="h",
		acao="exclusao definitiva",
		data_hora_exclusao=datetime(2024, 10, 2, 12, 0, 0),
		responsavel="usuario",
		motivo="pedido do titular",
	)

	with pytest.raises(ValidationError):
		LogExclusaoOut.model_validate(obj)


def test_log_exclusao_out_missing_email_hash_erro():
	"""Dispara erro quando 'email_hash' está ausente em LogExclusaoOut."""
	obj = make_obj(
		id=1,
		acao="exclusao definitiva",
		data_hora_exclusao=datetime(2024, 10, 2, 12, 0, 0),
		responsavel="usuario",
		motivo="pedido do titular",
	)

	with pytest.raises(ValidationError):
		LogExclusaoOut.model_validate(obj)

