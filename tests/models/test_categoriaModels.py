import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import session_factory, db, _criar_categoria

def test_metadata_tabela_categoria_esta_correta():
	"""Verifica metadados da tabela Categoria: colunas, nullability, UNIQUE e server_default."""
	from app.models.categoriaModels import Categoria

	table = Categoria.__table__
	assert Categoria.__tablename__ == "categoria"
	assert {c.name for c in table.columns} == {"id", "nome", "atualizado_em"}

	assert table.c.nome.nullable is False
	assert table.c.atualizado_em.nullable is False
	assert table.c.atualizado_em.server_default is not None

	assert table.c.nome.unique is True


def test_criacao_categoria_sucesso(db):
	"""Cria categoria e valida aplicação de defaults do servidor."""
	c = _criar_categoria(db, nome="Dados")
	assert c.id is not None
	assert getattr(c, "atualizado_em", None) is not None


def test_nome_obrigatorio_not_null(db):
	"""Garante NOT NULL para 'nome'."""
	from app.models.categoriaModels import Categoria

	with pytest.raises(IntegrityError):
		db.add(Categoria(nome=None))
		db.flush()


def test_nome_unique_viola_unicidade(db):
	"""Garante a unicidade do campo 'nome'."""
	_ = _criar_categoria(db, nome="AI")
	with pytest.raises(IntegrityError):
		_ = _criar_categoria(db, nome="AI")

