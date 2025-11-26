import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import (
	session_factory,
	db,
	_criar_curso,
	_criar_conhecimento,
	_criar_curso_conhecimento,
)

def test_metadata_curso_conhecimento_esta_correta():
	"""Valida metadados da tabela curso_conhecimento: colunas, NOT NULL, UNIQUE e FKs CASCADE."""
	from app.models.cursoConhecimentoModels import CursoConhecimento

	table = CursoConhecimento.__table__
	assert CursoConhecimento.__tablename__ == "curso_conhecimento"
	assert {c.name for c in table.columns} == {"id", "curso_id", "conhecimento_id"}

	assert table.c.curso_id.nullable is False
	assert table.c.conhecimento_id.nullable is False

	uniques = [c for c in table.constraints if getattr(c, "columns", None)]
	pares_unicos = [
		tuple(col.name for col in cons.columns)
		for cons in uniques
		if cons.name == "uq_curso_conhecimento"
	]
	assert ("curso_id", "conhecimento_id") in pares_unicos

	fks = list(table.foreign_keys)
	destinos = sorted((fk.column.table.name, fk.column.name, fk.ondelete) for fk in fks)
	assert ("curso", "id", "CASCADE") in destinos
	assert ("conhecimento", "id", "CASCADE") in destinos


def test_criacao_relacao_valida(db):
	"""Cria uma relação válida entre Curso e Conhecimento."""
	curso = _criar_curso(db, nome="Pandas", descricao="Análise de dados")
	know = _criar_conhecimento(db, nome="DataFrames")
	ck = _criar_curso_conhecimento(db, curso_id=curso.id, conhecimento_id=know.id)

	assert ck.id is not None
	assert ck.curso_id == curso.id
	assert ck.conhecimento_id == know.id


def test_unicidade_mesmo_curso_mesmo_conhecimento(db):
	"""Garante unicidade do par (curso_id, conhecimento_id)."""
	curso = _criar_curso(db, nome="FastAPI", descricao="APIs")
	know = _criar_conhecimento(db, nome="HTTP")
	_ = _criar_curso_conhecimento(db, curso_id=curso.id, conhecimento_id=know.id)

	with pytest.raises(IntegrityError):
		_ = _criar_curso_conhecimento(db, curso_id=curso.id, conhecimento_id=know.id)


def test_not_null_em_chaves_estrangeiras(db):
	"""Verifica NOT NULL em curso_id e conhecimento_id."""
	from app.models.cursoConhecimentoModels import CursoConhecimento

	with pytest.raises(IntegrityError):
		db.add(CursoConhecimento(curso_id=None, conhecimento_id=1))
		db.flush()

	with pytest.raises(IntegrityError):
		db.add(CursoConhecimento(curso_id=1, conhecimento_id=None))
		db.flush()


def test_cascade_delete_quando_remove_curso(db):
	"""Confere que excluir Curso remove o vínculo em curso_conhecimento (CASCADE)."""
	curso = _criar_curso(db, nome="SQL", descricao="Banco de dados")
	know = _criar_conhecimento(db, nome="Joins")
	ck = _criar_curso_conhecimento(db, curso_id=curso.id, conhecimento_id=know.id)

	from app.models.cursoModels import Curso
	db.delete(db.get(Curso, curso.id))
	db.flush()

	from app.models.cursoConhecimentoModels import CursoConhecimento
	assert db.get(CursoConhecimento, ck.id) is None


def test_cascade_delete_quando_remove_conhecimento(db):
	"""Confere que excluir Conhecimento remove o vínculo em curso_conhecimento (CASCADE)."""
	curso = _criar_curso(db, nome="Git", descricao="Controle de versão")
	know = _criar_conhecimento(db, nome="Merge")
	ck = _criar_curso_conhecimento(db, curso_id=curso.id, conhecimento_id=know.id)

	from app.models.conhecimentoModels import Conhecimento
	db.delete(db.get(Conhecimento, know.id))
	db.flush()

	from app.models.cursoConhecimentoModels import CursoConhecimento
	assert db.get(CursoConhecimento, ck.id) is None

