import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import session_factory, db, _criar_carreira

def test_metadata_tabela_carreira_esta_correta():
	"""Verifica metadados da tabela Carreira: colunas, nullability e server_default."""
	from app.models.carreiraModels import Carreira

	table = Carreira.__table__
	assert Carreira.__tablename__ == "carreira"
	assert {c.name for c in table.columns} == {"id", "nome", "descricao", "atualizado_em"}

	assert table.c.nome.nullable is False
	assert table.c.descricao.nullable is True
	assert table.c.atualizado_em.nullable is False

	assert table.c.atualizado_em.server_default is not None


def test_criacao_carreira_com_e_sem_descricao(db):
	"""Cria carreiras com e sem descrição e valida persistência."""
	c1 = _criar_carreira(db, nome="Backend", descricao="Constrói APIs")
	c2 = _criar_carreira(db, nome="Frontend", descricao=None)

	assert c1.id is not None and c1.descricao == "Constrói APIs"
	assert c2.id is not None and c2.descricao is None


def test_nome_obrigatorio_not_null(db):
	"""Garante que 'nome' é NOT NULL."""
	from app.models.carreiraModels import Carreira

	with pytest.raises(IntegrityError):
		db.add(Carreira(nome=None))
		db.flush()


def test_atualizado_em_preenchido_automaticamente(db):
	"""Confere preenchimento automático de 'atualizado_em' via server_default."""
	c = _criar_carreira(db, nome="Data")
	assert getattr(c, "atualizado_em", None) is not None

