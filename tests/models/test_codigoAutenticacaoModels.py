from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import session_factory, db, _criar_usuario, _criar_codigo

def test_metadata_tabela_codigo_autenticacao_esta_correta():
	"""Verifica metadados: colunas, nullability, default e FK CASCADE em CodigoAutenticacao."""
	from app.models.codigoAutenticacaoModels import CodigoAutenticacao

	table = CodigoAutenticacao.__table__
	assert CodigoAutenticacao.__tablename__ == "codigo_autenticacao"
	assert {c.name for c in table.columns} == {
		"id",
		"usuario_id",
		"codigo_recuperacao",
		"codigo_expira_em",
		"motivo",
	}

	assert table.c.usuario_id.nullable is False
	assert table.c.codigo_recuperacao.nullable is False
	assert table.c.codigo_expira_em.nullable is False
	assert table.c.motivo.nullable is False

	assert table.c.motivo.server_default is not None

	fks = list(table.foreign_keys)
	destinos = sorted((fk.column.table.name, fk.column.name, fk.ondelete) for fk in fks)
	assert ("usuario", "id", "CASCADE") in destinos


def test_criacao_codigo_valido_e_default_motivo(db):
	"""Cria código e verifica que 'motivo' recebe server_default quando não informado."""
	u = _criar_usuario(db)
	ca = _criar_codigo(db, usuario_id=u.id, codigo="XYZ", motivo=None)

	db.refresh(ca)
	assert ca.id is not None
	assert ca.motivo == "recuperacao_senha"


def test_not_null_campos_obrigatorios(db):
	"""Garante NOT NULL para usuario_id, codigo_recuperacao e codigo_expira_em."""
	from app.models.codigoAutenticacaoModels import CodigoAutenticacao
	u = _criar_usuario(db, nome="Bob", email="bob@example.com")
	expira = datetime.utcnow() + timedelta(minutes=30)

	with pytest.raises(IntegrityError):
		db.add(CodigoAutenticacao(usuario_id=None, codigo_recuperacao="C1", codigo_expira_em=expira))
		db.flush()

	with pytest.raises(IntegrityError):
		db.add(CodigoAutenticacao(usuario_id=u.id, codigo_recuperacao=None, codigo_expira_em=expira))
		db.flush()

	with pytest.raises(IntegrityError):
		db.add(CodigoAutenticacao(usuario_id=u.id, codigo_recuperacao="C2", codigo_expira_em=None))
		db.flush()


def test_fk_invalida_dispara_erro(db):
	"""Valida violação de FK quando usuario_id não existe."""
	with pytest.raises(IntegrityError):
		_ = _criar_codigo(db, usuario_id=999999, codigo="NOUSER")


def test_cascade_delete_quando_remove_usuario(db):
	"""Verifica CASCADE ao excluir usuario removendo códigos associados."""
	u = _criar_usuario(db, nome="Carol", email="carol@example.com")
	ca = _criar_codigo(db, usuario_id=u.id, codigo="CAROL1")

	from app.models.usuarioModels import Usuario
	db.delete(db.get(Usuario, u.id))
	db.flush()

	from app.models.codigoAutenticacaoModels import CodigoAutenticacao
	assert db.get(CodigoAutenticacao, ca.id) is None

