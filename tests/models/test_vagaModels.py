import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import session_factory, db, _criar_carreira, _criar_vaga


def test_metadata_vaga_esta_correta():
	"""Valida metadados de vaga: colunas, NOT NULL/UNIQUE/default e FK SET NULL."""
	from app.models.vagaModels import Vaga

	table = Vaga.__table__
	assert Vaga.__tablename__ == "vaga"
	assert {c.name for c in table.columns} == {"id", "titulo", "descricao", "criado_em", "carreira_id"}

	assert table.c.titulo.nullable is False
	assert table.c.descricao.nullable is False and table.c.descricao.unique is True
	assert table.c.criado_em.nullable is False and table.c.criado_em.server_default is not None
	assert table.c.carreira_id.nullable is True

	fks = list(table.foreign_keys)
	destinos = sorted((fk.column.table.name, fk.column.name, fk.ondelete) for fk in fks)
	assert ("carreira", "id", "SET NULL") in destinos


def test_criacao_vaga_sucesso(db):
	"""Cria vaga e valida preenchimento de criado_em."""
	v = _criar_vaga(db, titulo="Backend", descricao="Descricao1")
	assert v.id is not None
	assert getattr(v, "criado_em", None) is not None


def test_not_null_em_titulo_e_descricao(db):
	"""Garante NOT NULL para titulo e descricao."""
	from app.models.vagaModels import Vaga

	with pytest.raises(IntegrityError):
		db.add(Vaga(titulo=None, descricao="X"))
		db.flush()

	with pytest.raises(IntegrityError):
		db.add(Vaga(titulo="Y", descricao=None))
		db.flush()


def test_descricao_unique_viola_unicidade(db):
	"""Assegura UNIQUE para o campo descricao."""
	_ = _criar_vaga(db, titulo="A", descricao="UNIQ")
	with pytest.raises(IntegrityError):
		_ = _criar_vaga(db, titulo="B", descricao="UNIQ")


def test_ondelete_set_null_em_carreira(db):
	"""Confere que ao excluir Carreira o carreira_id da vaga vira NULL."""
	car = _criar_carreira(db, nome="Dados")
	v = _criar_vaga(db, titulo="Analista", descricao="D_ESC", carreira_id=car.id)

	from app.models.carreiraModels import Carreira
	db.delete(db.get(Carreira, car.id))
	db.flush()

	from app.models.vagaModels import Vaga
	v2 = db.get(Vaga, v.id)
	assert v2.carreira_id is None

