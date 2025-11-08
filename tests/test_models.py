"""
Testes do módulo app.models (ORM e relacionamentos)

Este arquivo valida constraints, relacionamentos e comportamentos padrão dos modelos:

- session (fixture):
	Cria um banco SQLite em memória com PRAGMA foreign_keys=ON, gera o schema a partir de Base
	antes dos testes e limpa após cada caso.

- test_habilidade_categoria_property_and_uniqueness:
	Verifica a propriedade `categoria` da Habilidade (retorna o nome da Categoria) e a
	unicidade de Habilidade por (nome, categoria_id) gerando IntegrityError em duplicatas.

- test_vaga_unique_descricao_and_carreira_relation:
	Confere relação Vaga->Carreira (e backref em carreira.vagas) e a unicidade do campo
	`descricao` em Vaga.

- test_usuario_relationships_and_unique_email:
	Valida relacionamentos Usuario->Carreira/Curso e unicidade do e-mail de Usuario.

- test_codigo_autenticacao_cascade_on_user_delete:
	Garante que a exclusão de Usuario faz CASCADE em CodigoAutenticacao associado.

- test_set_null_ondelete_usuario_and_vaga:
	Ao remover Carreira, os campos carreira_id em Usuario e Vaga são setados para NULL;
	ao remover Curso, usuario.curso_id é setado para NULL.

- test_relational_uniques_join_tables:
	Testa unicidade nas tabelas de junção: CursoConhecimento, CarreiraHabilidade,
	UsuarioHabilidade, ConhecimentoCategoria e VagaHabilidade.

- test_log_exclusao_defaults_and_normalizacao_unique:
	Verifica defaults de LogExclusao (acao, responsavel, motivo, data/hora) e unicidade
	em Normalizacao (campo `nome`/expressão regex).
"""

import os
from datetime import datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

# Env mínimos antes de importar app.*
os.environ.setdefault("KEY_CRYPT", "k")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("DB_USER", "u")
os.environ.setdefault("DB_PASSWORD", "p")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "db")

from app.models import (
	Base,
	Curso,
	Carreira,
	Usuario,
	Habilidade,
	Categoria,
	Conhecimento,
	Normalizacao,
	CodigoAutenticacao,
	LogExclusao,
	Vaga,
	CursoConhecimento,
	CarreiraHabilidade,
	UsuarioHabilidade,
	ConhecimentoCategoria,
	VagaHabilidade,
)


@pytest.fixture()
def session():
	engine = create_engine("sqlite+pysqlite:///:memory:")
	# Habilita FK para suportar ondelete CASCADE/SET NULL
	event.listen(engine, "connect", lambda dbapi_conn, _: dbapi_conn.execute("PRAGMA foreign_keys=ON"))
	TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	Base.metadata.create_all(bind=engine)
	db = TestingSessionLocal()
	try:
		yield db
	finally:
		db.close()
		Base.metadata.drop_all(bind=engine)


def test_habilidade_categoria_property_and_uniqueness(session):
	cat = Categoria(nome="Backend")
	session.add(cat)
	session.commit()
	session.refresh(cat)

	h = Habilidade(nome="Python", categoria_id=cat.id)
	session.add(h)
	session.commit()
	session.refresh(h)

	assert h.categoria == "Backend"

	dup = Habilidade(nome="Python", categoria_id=cat.id)
	session.add(dup)
	with pytest.raises(IntegrityError):
		session.commit()
	session.rollback()


def test_vaga_unique_descricao_and_carreira_relation(session):
	carreira = Carreira(nome="Dados", descricao="desc")
	session.add(carreira)
	session.commit()
	session.refresh(carreira)

	v = Vaga(titulo="X", descricao="descricao unica", carreira_id=carreira.id)
	session.add(v)
	session.commit()
	session.refresh(v)

	assert v.carreira is not None and v.carreira.id == carreira.id
	# backref
	assert any(v2.id == v.id for v2 in carreira.vagas)

	v2 = Vaga(titulo="Y", descricao="descricao unica", carreira_id=carreira.id)
	session.add(v2)
	with pytest.raises(IntegrityError):
		session.commit()
	session.rollback()


def test_usuario_relationships_and_unique_email(session):
	car = Carreira(nome="N", descricao="D")
	cur = Curso(nome="C", descricao="DD")
	session.add_all([car, cur])
	session.commit()
	session.refresh(car)
	session.refresh(cur)

	u = Usuario(nome="U", email="u@e.com", senha="S3nh@!", admin=False, carreira_id=car.id, curso_id=cur.id)
	session.add(u)
	session.commit()
	session.refresh(u)

	assert u.carreira and u.carreira.nome == "N"
	assert u.curso and u.curso.nome == "C"

	u_dup = Usuario(nome="U2", email="u@e.com", senha="Outra@1")
	session.add(u_dup)
	with pytest.raises(IntegrityError):
		session.commit()
	session.rollback()


def test_codigo_autenticacao_cascade_on_user_delete(session):
	u = Usuario(nome="U", email="u2@e.com", senha="S3nh@!", admin=False)
	session.add(u)
	session.commit()
	session.refresh(u)

	code = CodigoAutenticacao(usuario_id=u.id, codigo_recuperacao="123", codigo_expira_em=datetime(2025, 1, 1, 0, 0, 0), motivo="recuperacao_senha")
	session.add(code)
	session.commit()

	# Deleta usuário => deve CASCADE em codigo_autenticacao
	session.delete(u)
	session.commit()

	assert session.query(CodigoAutenticacao).count() == 0


def test_set_null_ondelete_usuario_and_vaga(session):
	car = Carreira(nome="Car", descricao="d")
	cur = Curso(nome="Cur", descricao="d")
	session.add_all([car, cur])
	session.commit()
	session.refresh(car)
	session.refresh(cur)

	u = Usuario(nome="U3", email="u3@e.com", senha="S3nh@!", admin=False, carreira_id=car.id, curso_id=cur.id)
	v = Vaga(titulo="T", descricao="desc unica abc", carreira_id=car.id)
	session.add_all([u, v])
	session.commit()
	session.refresh(u)
	session.refresh(v)

	# Remove carreira => SET NULL em usuario.carreira_id e vaga.carreira_id
	session.delete(car)
	session.commit()

	u_db = session.query(Usuario).filter(Usuario.id == u.id).first()
	v_db = session.query(Vaga).filter(Vaga.id == v.id).first()
	assert u_db is not None and u_db.carreira_id is None
	assert v_db is not None and v_db.carreira_id is None

	# Remove curso => SET NULL em usuario.curso_id
	session.delete(cur)
	session.commit()
	u_db2 = session.query(Usuario).filter(Usuario.id == u.id).first()
	assert u_db2 is not None and u_db2.curso_id is None


def test_relational_uniques_join_tables(session):
	# Base entities
	cur = Curso(nome="CUR", descricao="d")
	conh = Conhecimento(nome="Python")
	car = Carreira(nome="Eng", descricao="d")
	cat = Categoria(nome="Backend2")
	hab = Habilidade(nome="Flask", categoria_id=1)  # categoria ainda não persistida, ajustar após commit
	session.add_all([cur, conh, car, cat])
	session.commit()
	session.refresh(cur); session.refresh(conh); session.refresh(car); session.refresh(cat)

	# Corrige categoria_id da habilidade e persiste
	hab.categoria_id = cat.id
	session.add(hab)
	session.commit()
	session.refresh(hab)

	# CursoConhecimento unique
	cc = CursoConhecimento(curso_id=cur.id, conhecimento_id=conh.id)
	session.add(cc)
	session.commit()
	dup_cc = CursoConhecimento(curso_id=cur.id, conhecimento_id=conh.id)
	session.add(dup_cc)
	with pytest.raises(IntegrityError):
		session.commit()
	session.rollback()

	# CarreiraHabilidade unique
	ch = CarreiraHabilidade(carreira_id=car.id, habilidade_id=hab.id)
	session.add(ch)
	session.commit()
	dup_ch = CarreiraHabilidade(carreira_id=car.id, habilidade_id=hab.id)
	session.add(dup_ch)
	with pytest.raises(IntegrityError):
		session.commit()
	session.rollback()

	# UsuarioHabilidade unique
	u = Usuario(nome="U4", email="u4@e.com", senha="S3nh@!", admin=False)
	session.add(u)
	session.commit(); session.refresh(u)
	uh = UsuarioHabilidade(usuario_id=u.id, habilidade_id=hab.id)
	session.add(uh); session.commit()
	dup_uh = UsuarioHabilidade(usuario_id=u.id, habilidade_id=hab.id)
	session.add(dup_uh)
	with pytest.raises(IntegrityError):
		session.commit()
	session.rollback()

	# ConhecimentoCategoria unique
	kc = ConhecimentoCategoria(conhecimento_id=conh.id, categoria_id=cat.id, peso=None)
	session.add(kc); session.commit()
	dup_kc = ConhecimentoCategoria(conhecimento_id=conh.id, categoria_id=cat.id, peso=None)
	session.add(dup_kc)
	with pytest.raises(IntegrityError):
		session.commit()
	session.rollback()

	# VagaHabilidade unique
	v = Vaga(titulo="VT", descricao="desc v 1")
	session.add(v); session.commit(); session.refresh(v)
	vh = VagaHabilidade(vaga_id=v.id, habilidade_id=hab.id)
	session.add(vh); session.commit()
	dup_vh = VagaHabilidade(vaga_id=v.id, habilidade_id=hab.id)
	session.add(dup_vh)
	with pytest.raises(IntegrityError):
		session.commit()
	session.rollback()


def test_log_exclusao_defaults_and_normalizacao_unique(session):
	log = LogExclusao(email_hash="abc")
	session.add(log)
	session.commit()
	session.refresh(log)

	assert log.id is not None
	assert log.acao == "exclusao definitiva"
	assert log.responsavel == "usuario"
	assert log.motivo == "pedido do titular"
	assert log.data_hora_exclusao is not None

	n1 = Normalizacao(nome=r"^node(js)?$", nome_padronizado="Node.js")
	session.add(n1); session.commit()
	dup = Normalizacao(nome=r"^node(js)?$", nome_padronizado="NodeJS")
	session.add(dup)
	with pytest.raises(IntegrityError):
		session.commit()
	session.rollback()

