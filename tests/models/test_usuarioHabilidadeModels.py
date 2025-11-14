import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import (
	session_factory,
	db,
	_criar_categoria,
	_criar_habilidade,
	_criar_usuario,
	_criar_usuario_habilidade,
)


def test_metadata_usuario_habilidade_esta_correta():
	"""Valida metadados de usuario_habilidade: colunas, NOT NULL, UNIQUE e FKs CASCADE."""
	from app.models.usuarioHabilidadeModels import UsuarioHabilidade

	table = UsuarioHabilidade.__table__
	assert UsuarioHabilidade.__tablename__ == "usuario_habilidade"
	assert {c.name for c in table.columns} == {"id", "usuario_id", "habilidade_id"}

	assert table.c.usuario_id.nullable is False
	assert table.c.habilidade_id.nullable is False

	uniques = [c for c in table.constraints if getattr(c, "columns", None)]
	pares_unicos = [
		tuple(col.name for col in cons.columns)
		for cons in uniques
		if cons.name == "uq_usuario_habilidade"
	]
	assert ("usuario_id", "habilidade_id") in pares_unicos

	fks = list(table.foreign_keys)
	destinos = sorted((fk.column.table.name, fk.column.name, fk.ondelete) for fk in fks)
	assert ("usuario", "id", "CASCADE") in destinos
	assert ("habilidade", "id", "CASCADE") in destinos


def test_criacao_relacao_valida(db):
	"""Cria relação válida entre Usuario e Habilidade."""
	u = _criar_usuario(db)
	h = _criar_habilidade(db)
	uh = _criar_usuario_habilidade(db, usuario_id=u.id, habilidade_id=h.id)

	assert uh.id is not None
	assert uh.usuario_id == u.id
	assert uh.habilidade_id == h.id


def test_unicidade_mesmo_usuario_mesma_habilidade(db):
	"""Garante unicidade do par (usuario_id, habilidade_id)."""
	u = _criar_usuario(db, nome="Bob", email="bob@example.com")
	h = _criar_habilidade(db, nome="Pandas")
	_ = _criar_usuario_habilidade(db, usuario_id=u.id, habilidade_id=h.id)

	with pytest.raises(IntegrityError):
		_ = _criar_usuario_habilidade(db, usuario_id=u.id, habilidade_id=h.id)


def test_not_null_em_chaves_estrangeiras(db):
	"""Verifica NOT NULL em usuario_id e habilidade_id."""
	from app.models.usuarioHabilidadeModels import UsuarioHabilidade

	with pytest.raises(IntegrityError):
		db.add(UsuarioHabilidade(usuario_id=None, habilidade_id=1))
		db.flush()

	with pytest.raises(IntegrityError):
		db.add(UsuarioHabilidade(usuario_id=1, habilidade_id=None))
		db.flush()


def test_cascade_delete_quando_remove_usuario(db):
	"""Confere CASCADE ao excluir Usuario removendo vínculos em usuario_habilidade."""
	u = _criar_usuario(db, nome="Carol", email="carol@example.com")
	h = _criar_habilidade(db, nome="HTTP")
	uh = _criar_usuario_habilidade(db, usuario_id=u.id, habilidade_id=h.id)

	from app.models.usuarioModels import Usuario
	db.delete(db.get(Usuario, u.id))
	db.flush()

	from app.models.usuarioHabilidadeModels import UsuarioHabilidade
	assert db.get(UsuarioHabilidade, uh.id) is None


def test_cascade_delete_quando_remove_habilidade(db):
	"""Confere CASCADE ao excluir Habilidade removendo vínculos em usuario_habilidade."""
	u = _criar_usuario(db, nome="Dave", email="dave@example.com")
	h = _criar_habilidade(db, nome="Docker")
	uh = _criar_usuario_habilidade(db, usuario_id=u.id, habilidade_id=h.id)

	from app.models.habilidadeModels import Habilidade
	db.delete(db.get(Habilidade, h.id))
	db.flush()

	from app.models.usuarioHabilidadeModels import UsuarioHabilidade
	assert db.get(UsuarioHabilidade, uh.id) is None

