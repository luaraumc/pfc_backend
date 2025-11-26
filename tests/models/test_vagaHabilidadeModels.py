import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import (
	session_factory,
	db,
	_criar_categoria,
	_criar_habilidade,
	_criar_vaga,
	_criar_vaga_habilidade,
)


def test_metadata_vaga_habilidade_esta_correta():
	"""Valida metadados de vaga_habilidade: colunas, NOT NULL, UNIQUE e FKs CASCADE."""
	from app.models.vagaHabilidadeModels import VagaHabilidade

	table = VagaHabilidade.__table__
	assert VagaHabilidade.__tablename__ == "vaga_habilidade"
	assert {c.name for c in table.columns} == {"id", "vaga_id", "habilidade_id"}

	assert table.c.vaga_id.nullable is False
	assert table.c.habilidade_id.nullable is False

	uniques = [c for c in table.constraints if getattr(c, "columns", None)]
	pares_unicos = [
		tuple(col.name for col in cons.columns)
		for cons in uniques
		if cons.name == "uq_vaga_habilidade"
	]
	assert ("vaga_id", "habilidade_id") in pares_unicos

	fks = list(table.foreign_keys)
	destinos = sorted((fk.column.table.name, fk.column.name, fk.ondelete) for fk in fks)
	assert ("vaga", "id", "CASCADE") in destinos
	assert ("habilidade", "id", "CASCADE") in destinos


def test_criacao_relacao_valida(db):
	"""Cria relação válida entre Vaga e Habilidade."""
	vaga = _criar_vaga(db, titulo="Backend", descricao="D1")
	hab = _criar_habilidade(db, nome="FastAPI")
	vh = _criar_vaga_habilidade(db, vaga_id=vaga.id, habilidade_id=hab.id)

	assert vh.id is not None
	assert vh.vaga_id == vaga.id
	assert vh.habilidade_id == hab.id


def test_unicidade_mesma_vaga_mesma_habilidade(db):
	"""Garante unicidade do par (vaga_id, habilidade_id)."""
	vaga = _criar_vaga(db, titulo="Dados", descricao="D2")
	hab = _criar_habilidade(db, nome="Pandas")
	_ = _criar_vaga_habilidade(db, vaga_id=vaga.id, habilidade_id=hab.id)

	with pytest.raises(IntegrityError):
		_ = _criar_vaga_habilidade(db, vaga_id=vaga.id, habilidade_id=hab.id)


def test_not_null_em_chaves_estrangeiras(db):
	"""Verifica NOT NULL em vaga_id e habilidade_id."""
	from app.models.vagaHabilidadeModels import VagaHabilidade

	with pytest.raises(IntegrityError):
		db.add(VagaHabilidade(vaga_id=None, habilidade_id=1))
		db.flush()

	with pytest.raises(IntegrityError):
		db.add(VagaHabilidade(vaga_id=1, habilidade_id=None))
		db.flush()


def test_cascade_delete_quando_remove_vaga(db):
	"""Confere CASCADE ao excluir Vaga removendo vínculos em vaga_habilidade."""
	vaga = _criar_vaga(db, titulo="Mobile", descricao="D3")
	hab = _criar_habilidade(db, nome="Kotlin")
	vh = _criar_vaga_habilidade(db, vaga_id=vaga.id, habilidade_id=hab.id)

	from app.models.vagaModels import Vaga
	db.delete(db.get(Vaga, vaga.id))
	db.flush()

	from app.models.vagaHabilidadeModels import VagaHabilidade
	assert db.get(VagaHabilidade, vh.id) is None


def test_cascade_delete_quando_remove_habilidade(db):
	"""Confere CASCADE ao excluir Habilidade removendo vínculos em vaga_habilidade."""
	vaga = _criar_vaga(db, titulo="DevOps", descricao="D4")
	hab = _criar_habilidade(db, nome="Docker")
	vh = _criar_vaga_habilidade(db, vaga_id=vaga.id, habilidade_id=hab.id)

	from app.models.habilidadeModels import Habilidade
	db.delete(db.get(Habilidade, hab.id))
	db.flush()

	from app.models.vagaHabilidadeModels import VagaHabilidade
	assert db.get(VagaHabilidade, vh.id) is None

