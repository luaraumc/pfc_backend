import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import session_factory, db, _criar_curso


def test_metadata_tabela_curso_esta_correta():
	"""Verifica metadados da tabela curso: colunas, NOT NULL e default de atualizado_em."""
	from app.models.cursoModels import Curso

	table = Curso.__table__
	assert Curso.__tablename__ == "curso"
	assert {c.name for c in table.columns} == {"id", "nome", "descricao", "atualizado_em"}

	assert table.c.nome.nullable is False
	assert table.c.descricao.nullable is False
	assert table.c.atualizado_em.nullable is False
	assert table.c.atualizado_em.server_default is not None


def test_criacao_curso_sucesso(db):
	"""Cria um curso e valida preenchimento de atualizado_em."""
	c = _criar_curso(db, nome="FastAPI", descricao="APIs com Python")
	assert c.id is not None
	assert getattr(c, "atualizado_em", None) is not None


def test_nome_obrigatorio_not_null(db):
	"""Garante NOT NULL para o campo nome."""
	from app.models.cursoModels import Curso

	with pytest.raises(IntegrityError):
		db.add(Curso(nome=None, descricao="ok"))
		db.flush()


def test_descricao_obrigatoria_not_null(db):
	"""Garante NOT NULL para o campo descricao."""
	from app.models.cursoModels import Curso

	with pytest.raises(IntegrityError):
		db.add(Curso(nome="Curso", descricao=None))
		db.flush()

