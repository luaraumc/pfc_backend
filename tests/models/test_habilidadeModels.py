import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import (
	session_factory,
	db,
	_criar_categoria,
	_criar_habilidade,
)


def test_metadata_tabela_habilidade_esta_correta():
	"""Valida metadados de habilidade: colunas, NOT NULL, UNIQUE e FK RESTRICT."""
	from app.models.habilidadeModels import Habilidade

	table = Habilidade.__table__
	assert Habilidade.__tablename__ == "habilidade"
	assert {c.name for c in table.columns} == {"id", "nome", "categoria_id", "atualizado_em"}

	assert table.c.nome.nullable is False
	assert table.c.nome.unique is True
	assert table.c.categoria_id.nullable is False
	assert table.c.atualizado_em.nullable is False
	assert table.c.atualizado_em.server_default is not None

	fks = list(table.foreign_keys)
	destinos = sorted((fk.column.table.name, fk.column.name, fk.ondelete) for fk in fks)
	assert ("categoria", "id", "RESTRICT") in destinos


def test_criacao_habilidade_e_propriedade_categoria(db):
	"""Cria habilidade relacionada e valida propriedade 'categoria' com o nome da categoria."""
	cat = _criar_categoria(db, nome="Dados")
	h = _criar_habilidade(db, nome="Pandas", categoria=cat)

	db.refresh(h)
	assert h.id is not None
	assert h.categoria_id == cat.id
	assert h.categoria == "Dados"


def test_unicidade_nome_global(db):
	"""Assegura que o nome da habilidade é globalmente único."""
	_ = _criar_categoria(db, nome="ML")
	h1 = _criar_habilidade(db, nome="Scikit", categoria=None)

	with pytest.raises(IntegrityError):
		outra_cat = _criar_categoria(db, nome="Web")
		_ = _criar_habilidade(db, nome=h1.nome, categoria=outra_cat)


def test_not_null_nome_e_categoria_id(db):
	"""Verifica NOT NULL em nome e categoria_id."""
	from app.models.habilidadeModels import Habilidade

	cat = _criar_categoria(db, nome="Cloud")
	with pytest.raises(IntegrityError):
		db.add(Habilidade(nome=None, categoria_id=cat.id))
		db.flush()

	with pytest.raises(IntegrityError):
		db.add(Habilidade(nome="AWS", categoria_id=None))
		db.flush()


def test_ondelete_restrict_nao_permite_excluir_categoria_com_habilidade(db):
	"""Garante que RESTRICT impede excluir categoria enquanto houver habilidades associadas."""
	cat = _criar_categoria(db, nome="Mobile")
	_ = _criar_habilidade(db, nome="Kotlin", categoria=cat)

	from app.models.categoriaModels import Categoria
	with pytest.raises(IntegrityError):
		db.delete(db.get(Categoria, cat.id))
		db.flush()

	from app.models.habilidadeModels import Habilidade
	for h in db.query(Habilidade).filter(Habilidade.categoria_id == cat.id).all():
		db.delete(h)
	db.flush()

	db.delete(db.get(Categoria, cat.id))
	db.flush()

