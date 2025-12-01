import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import (
    session_factory,
    db,
    _criar_categoria,
    _criar_habilidade,
    _criar_carreira,
    _criar_carreira_habilidade,
)

def test_metadata_da_tabela_esta_correta():
	"""Verifica metadados da tabela CarreiraHabilidade: colunas, nullability, UNIQUE e FKs CASCADE."""
	from app.models.carreiraHabilidadeModels import CarreiraHabilidade

	table = CarreiraHabilidade.__table__

	assert CarreiraHabilidade.__tablename__ == "carreira_habilidade"
	assert {c.name for c in table.columns} == {"id", "frequencia", "carreira_id", "habilidade_id"}

	assert table.c.frequencia.nullable is True
	assert table.c.carreira_id.nullable is False
	assert table.c.habilidade_id.nullable is False

	uniques = [c for c in table.constraints if getattr(c, "columns", None)]
	pares_unicos = [
		tuple(col.name for col in cons.columns)
		for cons in uniques
		if cons.name == "uq_carreira_habilidade"
	]
	assert ("carreira_id", "habilidade_id") in pares_unicos

	fks = list(table.foreign_keys)
	destinos = sorted((fk.column.table.name, fk.column.name, fk.ondelete) for fk in fks)
	assert ("carreira", "id", "CASCADE") in destinos
	assert ("habilidade", "id", "CASCADE") in destinos


def test_criacao_sucesso_com_frequencia_opcional(db):
	"""Cria relação carreira-habilidade com frequencia opcional e valida persistência."""
	car = _criar_carreira(db, nome="Backend")
	hab = _criar_habilidade(db, nome="FastAPI")

	ch = _criar_carreira_habilidade(db, carreira_id=car.id, habilidade_id=hab.id, frequencia=None)

	assert ch.id is not None
	assert ch.frequencia is None
	assert ch.carreira_id == car.id
	assert ch.habilidade_id == hab.id


def test_violacao_de_unicidade_mesma_carreira_mesma_habilidade(db):
	"""Garante UNIQUE no par (carreira_id, habilidade_id)."""
	car = _criar_carreira(db, nome="Dados")
	hab = _criar_habilidade(db, nome="Pandas")
	_ = _criar_carreira_habilidade(db, carreira_id=car.id, habilidade_id=hab.id, frequencia=5)

	with pytest.raises(IntegrityError):
		_ = _criar_carreira_habilidade(db, carreira_id=car.id, habilidade_id=hab.id, frequencia=10)


def test_not_null_em_chaves_estrangeiras(db):
	"""Garante NOT NULL para carreira_id e habilidade_id."""
	from app.models.carreiraHabilidadeModels import CarreiraHabilidade

	with pytest.raises(IntegrityError):
		db.add(CarreiraHabilidade(carreira_id=None, habilidade_id=1))
		db.flush()

	with pytest.raises(IntegrityError):
		db.add(CarreiraHabilidade(carreira_id=1, habilidade_id=None))
		db.flush()


def test_cascade_delete_quando_remove_carreira(db):
	"""Verifica CASCADE ao excluir carreira removendo a relação associativa."""
	car = _criar_carreira(db, nome="Mobile")
	hab = _criar_habilidade(db, nome="Kotlin")
	ch = _criar_carreira_habilidade(db, carreira_id=car.id, habilidade_id=hab.id)

	from app.models.carreiraModels import Carreira
	db.delete(db.get(Carreira, car.id))
	db.flush()

	from app.models.carreiraHabilidadeModels import CarreiraHabilidade
	assert db.get(CarreiraHabilidade, ch.id) is None


def test_cascade_delete_quando_remove_habilidade(db):
	"""Verifica CASCADE ao excluir habilidade removendo a relação associativa."""
	car = _criar_carreira(db, nome="QA")
	hab = _criar_habilidade(db, nome="PyTest")
	ch = _criar_carreira_habilidade(db, carreira_id=car.id, habilidade_id=hab.id)

	from app.models.habilidadeModels import Habilidade
	db.delete(db.get(Habilidade, hab.id))
	db.flush()

	from app.models.carreiraHabilidadeModels import CarreiraHabilidade
	assert db.get(CarreiraHabilidade, ch.id) is None

