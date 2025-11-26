import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import session_factory, db, _criar_log

def test_metadata_log_exclusao_esta_correta():
	"""Valida metadados de log_exclusoes: colunas, NOT NULL/defaults, tamanho e índice."""
	from app.models.logExclusaoModels import LogExclusao

	table = LogExclusao.__table__
	assert LogExclusao.__tablename__ == "log_exclusoes"
	assert {c.name for c in table.columns} == {
		"id",
		"email_hash",
		"acao",
		"data_hora_exclusao",
		"responsavel",
		"motivo",
	}

	assert table.c.email_hash.nullable is False
	assert table.c.acao.nullable is False and table.c.acao.server_default is not None
	assert table.c.data_hora_exclusao.nullable is False and table.c.data_hora_exclusao.server_default is not None
	assert table.c.responsavel.nullable is False and table.c.responsavel.server_default is not None
	assert table.c.motivo.nullable is False and table.c.motivo.server_default is not None
	assert getattr(table.c.email_hash.type, "length", None) == 128

	indexed_cols = []
	for idx in table.indexes:
		indexed_cols.extend(col.name for col in idx.columns)
	assert "email_hash" in indexed_cols


def test_criacao_minima_preenche_defaults(db):
	"""Cria registro mínimo e verifica aplicação dos defaults de servidor."""
	log = _criar_log(db, email_hash="abc")
	db.refresh(log)
	assert log.id is not None
	assert log.email_hash == "abc"
	assert log.acao == "exclusao definitiva"
	assert log.responsavel == "usuario"
	assert log.motivo == "pedido do titular"
	assert getattr(log, "data_hora_exclusao", None) is not None


def test_not_null_email_hash(db):
	"""Garante NOT NULL para o campo email_hash."""
	from app.models.logExclusaoModels import LogExclusao

	with pytest.raises(IntegrityError):
		db.add(LogExclusao(email_hash=None))
		db.flush()

