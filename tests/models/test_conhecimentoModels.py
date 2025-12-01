import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import session_factory, db, _criar_conhecimento

def test_metadata_tabela_conhecimento_esta_correta():
	"""Verifica metadados da tabela Conhecimento: colunas, nullability, UNIQUE e server_default."""
	from app.models.conhecimentoModels import Conhecimento

	table = Conhecimento.__table__
	assert Conhecimento.__tablename__ == "conhecimento"
	assert {c.name for c in table.columns} == {"id", "nome", "atualizado_em"}

	assert table.c.nome.nullable is False
	assert table.c.nome.unique is True
	assert table.c.atualizado_em.nullable is False
	assert table.c.atualizado_em.server_default is not None


def test_criacao_conhecimento_sucesso(db):
	"""Cria conhecimento e valida aplicação de defaults do servidor."""
	k = _criar_conhecimento(db, nome="Estruturas de Dados")
	assert k.id is not None
	assert getattr(k, "atualizado_em", None) is not None


def test_nome_obrigatorio_not_null(db):
	"""Garante NOT NULL para 'nome'."""
	from app.models.conhecimentoModels import Conhecimento

	with pytest.raises(IntegrityError):
		db.add(Conhecimento(nome=None))
		db.flush()


def test_nome_unique_viola_unicidade(db):
	"""Garante unicidade do campo 'nome'."""
	_ = _criar_conhecimento(db, nome="Redes")
	with pytest.raises(IntegrityError):
		_ = _criar_conhecimento(db, nome="Redes")

