import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import (
    session_factory,
    db,
    _criar_categoria,
    _criar_conhecimento,
    _criar_conhecimento_categoria,
)

def test_metadata_conhecimento_categoria_esta_correta():
	"""Verifica metadados: colunas, nullability, UNIQUE par e FKs CASCADE em ConhecimentoCategoria."""
	from app.models.conhecimentoCategoriaModels import ConhecimentoCategoria

	table = ConhecimentoCategoria.__table__
	assert ConhecimentoCategoria.__tablename__ == "conhecimento_categoria"
	assert {c.name for c in table.columns} == {"id", "conhecimento_id", "categoria_id", "peso"}

	assert table.c.conhecimento_id.nullable is False
	assert table.c.categoria_id.nullable is False
	assert table.c.peso.nullable is True

	uniques = [c for c in table.constraints if getattr(c, "columns", None)]
	pares_unicos = [
		tuple(col.name for col in cons.columns)
		for cons in uniques
		if cons.name == "uq_conhecimento_categoria"
	]
	assert ("conhecimento_id", "categoria_id") in pares_unicos

	fks = list(table.foreign_keys)
	destinos = sorted((fk.column.table.name, fk.column.name, fk.ondelete) for fk in fks)
	assert ("conhecimento", "id", "CASCADE") in destinos
	assert ("categoria", "id", "CASCADE") in destinos


def test_criacao_sucesso_com_peso_opcional(db):
	"""Cria relação com peso opcional e valida persistência."""
	cat = _criar_categoria(db, nome="Dados")
	kn = _criar_conhecimento(db, nome="ETL")
	kc = _criar_conhecimento_categoria(db, conhecimento_id=kn.id, categoria_id=cat.id, peso=None)

	assert kc.id is not None
	assert kc.peso is None
	assert kc.conhecimento_id == kn.id
	assert kc.categoria_id == cat.id


def test_unicidade_mesmo_conhecimento_mesma_categoria(db):
	"""Garante UNIQUE no par (conhecimento_id, categoria_id)."""
	cat = _criar_categoria(db, nome="Web")
	kn = _criar_conhecimento(db, nome="HTTP")
	_ = _criar_conhecimento_categoria(db, conhecimento_id=kn.id, categoria_id=cat.id, peso=3)

	with pytest.raises(IntegrityError):
		_ = _criar_conhecimento_categoria(db, conhecimento_id=kn.id, categoria_id=cat.id, peso=7)


def test_not_null_em_chaves_estrangeiras(db):
	"""Garante NOT NULL para chaves estrangeiras conhecimento_id e categoria_id."""
	from app.models.conhecimentoCategoriaModels import ConhecimentoCategoria

	with pytest.raises(IntegrityError):
		db.add(ConhecimentoCategoria(conhecimento_id=None, categoria_id=1))
		db.flush()

	with pytest.raises(IntegrityError):
		db.add(ConhecimentoCategoria(conhecimento_id=1, categoria_id=None))
		db.flush()


def test_cascade_delete_quando_remove_conhecimento(db):
	"""Verifica CASCADE ao excluir conhecimento removendo a relação associativa."""
	cat = _criar_categoria(db, nome="ML")
	kn = _criar_conhecimento(db, nome="Regressão")
	kc = _criar_conhecimento_categoria(db, conhecimento_id=kn.id, categoria_id=cat.id)

	from app.models.conhecimentoModels import Conhecimento
	db.delete(db.get(Conhecimento, kn.id))
	db.flush()

	from app.models.conhecimentoCategoriaModels import ConhecimentoCategoria
	assert db.get(ConhecimentoCategoria, kc.id) is None


def test_cascade_delete_quando_remove_categoria(db):
	"""Verifica CASCADE ao excluir categoria removendo a relação associativa."""
	cat = _criar_categoria(db, nome="Cloud")
	kn = _criar_conhecimento(db, nome="S3")
	kc = _criar_conhecimento_categoria(db, conhecimento_id=kn.id, categoria_id=cat.id)

	from app.models.categoriaModels import Categoria
	db.delete(db.get(Categoria, cat.id))
	db.flush()

	from app.models.conhecimentoCategoriaModels import ConhecimentoCategoria
	assert db.get(ConhecimentoCategoria, kc.id) is None
