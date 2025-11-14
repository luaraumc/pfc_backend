import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import session_factory, db


def _criar_normalizacao(db, nome="^node(js)?$", nome_padronizado="Node.js"):
	"""Helper: cria e persiste uma Normalizacao para uso nos testes."""
	from app.models.normalizacaoModels import Normalizacao

	n = Normalizacao(nome=nome, nome_padronizado=nome_padronizado)
	db.add(n)
	db.flush()
	return n


def test_metadata_tabela_normalizacao_esta_correta():
	"""Valida metadados de normalizacao: colunas, NOT NULL, UNIQUE e default de atualizado_em."""
	from app.models.normalizacaoModels import Normalizacao

	table = Normalizacao.__table__
	assert Normalizacao.__tablename__ == "normalizacao"
	assert {c.name for c in table.columns} == {"id", "nome", "nome_padronizado", "atualizado_em"}

	assert table.c.nome.nullable is False
	assert table.c.nome.unique is True
	assert table.c.nome_padronizado.nullable is False
	assert table.c.atualizado_em.nullable is False
	assert table.c.atualizado_em.server_default is not None


def test_criacao_normalizacao_sucesso(db):
	"""Cria uma normalizacao e valida os campos preenchidos."""
	n = _criar_normalizacao(db, nome=r"^py(thon)?$", nome_padronizado="Python")
	assert n.id is not None
	assert n.nome == r"^py(thon)?$"
	assert n.nome_padronizado == "Python"
	assert getattr(n, "atualizado_em", None) is not None


def test_not_null_campos_obrigatorios(db):
	"""Garante NOT NULL para nome e nome_padronizado."""
	from app.models.normalizacaoModels import Normalizacao

	with pytest.raises(IntegrityError):
		db.add(Normalizacao(nome=None, nome_padronizado="X"))
		db.flush()

	with pytest.raises(IntegrityError):
		db.add(Normalizacao(nome="^x$", nome_padronizado=None))
		db.flush()


def test_nome_unique_viola_unicidade(db):
	"""Assegura que o campo nome é único (UNIQUE)."""
	_ = _criar_normalizacao(db, nome=r"^go(lang)?$", nome_padronizado="Go")
	with pytest.raises(IntegrityError):
		_ = _criar_normalizacao(db, nome=r"^go(lang)?$", nome_padronizado="GoLang")

