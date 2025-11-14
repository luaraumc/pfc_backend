import pytest
from sqlalchemy.exc import IntegrityError

from utils_test_models import (
	session_factory,
	db,
	_criar_carreira,
	_criar_curso,
	_criar_usuario,
)


def test_metadata_usuario_esta_correta():
	"""Valida metadados de usuario: colunas, NOT NULL/UNIQUE/defaults e FKs SET NULL."""
	from app.models.usuarioModels import Usuario

	table = Usuario.__table__
	assert Usuario.__tablename__ == "usuario"
	assert {c.name for c in table.columns} == {
		"id",
		"nome",
		"email",
		"senha",
		"admin",
		"carreira_id",
		"curso_id",
		"criado_em",
		"atualizado_em",
	}


	assert table.c.nome.nullable is False
	assert table.c.email.nullable is False and table.c.email.unique is True
	assert table.c.senha.nullable is False
	assert table.c.admin.nullable is False and table.c.admin.default is not None
	assert table.c.carreira_id.nullable is True
	assert table.c.curso_id.nullable is True
	assert table.c.criado_em.nullable is False and table.c.criado_em.server_default is not None
	assert table.c.atualizado_em.nullable is False and table.c.atualizado_em.server_default is not None

	fks = list(table.foreign_keys)
	destinos = sorted((fk.column.table.name, fk.column.name, fk.ondelete) for fk in fks)
	assert ("carreira", "id", "SET NULL") in destinos
	assert ("curso", "id", "SET NULL") in destinos


def test_criacao_usuario_valores_default(db):
	"""Cria usuário e valida defaults (admin False, timestamps preenchidos)."""
	u = _criar_usuario(db)
	db.refresh(u)
	assert u.id is not None
	assert u.admin is False
	assert u.carreira_id is None and u.curso_id is None
	assert getattr(u, "criado_em", None) is not None
	assert getattr(u, "atualizado_em", None) is not None


def test_not_null_campos_obrigatorios(db):
	"""Garante NOT NULL em nome, email e senha."""
	from app.models.usuarioModels import Usuario

	with pytest.raises(IntegrityError):
		db.add(Usuario(nome=None, email="a@a", senha="x"))
		db.flush()

	with pytest.raises(IntegrityError):
		db.add(Usuario(nome="A", email=None, senha="x"))
		db.flush()

	with pytest.raises(IntegrityError):
		db.add(Usuario(nome="A", email="a@a", senha=None))
		db.flush()


def test_email_unique_viola_unicidade(db):
	"""Assegura UNIQUE para o campo email."""
	_ = _criar_usuario(db, email="dup@example.com")
	with pytest.raises(IntegrityError):
		_ = _criar_usuario(db, email="dup@example.com")


def test_ondelete_set_null_para_carreira(db):
	"""Confere que ao excluir Carreira o campo carreira_id do usuário vira NULL."""
	car = _criar_carreira(db, nome="Dados")
	u = _criar_usuario(db, nome="Bob", email="bob@example.com", carreira_id=car.id)

	from app.models.carreiraModels import Carreira
	db.delete(db.get(Carreira, car.id))
	db.flush()

	from app.models.usuarioModels import Usuario
	u2 = db.get(Usuario, u.id)
	assert u2.carreira_id is None


def test_ondelete_set_null_para_curso(db):
	"""Confere que ao excluir Curso o campo curso_id do usuário vira NULL."""
	curso = _criar_curso(db, nome="Algoritmos", descricao="Base")
	u = _criar_usuario(db, nome="Carol", email="carol@example.com", curso_id=curso.id)

	from app.models.cursoModels import Curso
	db.delete(db.get(Curso, curso.id))
	db.flush()

	from app.models.usuarioModels import Usuario
	u2 = db.get(Usuario, u.id)
	assert u2.curso_id is None

