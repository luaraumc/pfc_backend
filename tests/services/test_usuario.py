import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Variáveis mínimas de ambiente para evitar erros nas imports
os.environ.setdefault("KEY_CRYPT", "test-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "testdb")

from app.dependencies import Base
from app.schemas import UsuarioBase, UsuarioOut
from app.services.usuario import (
	criar_usuario,
	listar_usuarios,
	buscar_usuario_por_id,
	buscar_usuario_por_email,
	atualizar_usuario,
	atualizar_senha,
	deletar_usuario,
)


@pytest.fixture(scope="function")
def session():
	engine = create_engine("sqlite+pysqlite:///:memory:", echo=False, future=True)
	TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	Base.metadata.create_all(bind=engine)
	db = TestingSessionLocal()
	try:
		yield db
	finally:
		db.close()
		Base.metadata.drop_all(bind=engine)


def _payload(
	nome="Usuário Teste",
	email="user@test.com",
	senha="Senha1!",
	admin=False,
	carreira_id=None,
	curso_id=None,
) -> UsuarioBase:
	return UsuarioBase(
		nome=nome,
		email=email,
		senha=senha,
		admin=admin,
		carreira_id=carreira_id,
		curso_id=curso_id,
	)


def test_listar_usuarios_vazio(session):
	itens = listar_usuarios(session)
	assert isinstance(itens, list)
	assert itens == []


def test_criar_usuario(session):
	out = criar_usuario(session, _payload())
	assert isinstance(out, UsuarioOut)
	assert out.id is not None
	assert out.nome == "Usuário Teste"
	assert out.email == "user@test.com"
	assert out.admin is False


def test_listar_usuarios_populado(session):
	criar_usuario(session, _payload("Alice", "alice@test.com"))
	criar_usuario(session, _payload("Bob", "bob@test.com"))
	itens = listar_usuarios(session)
	nomes = {i.nome for i in itens}
	assert len(itens) == 2
	assert {"Alice", "Bob"}.issubset(nomes)


def test_buscar_usuario_por_id(session):
	criado = criar_usuario(session, _payload("Carol", "carol@test.com"))
	achado = buscar_usuario_por_id(session, criado.id)
	assert achado is not None
	assert achado.id == criado.id
	assert achado.email == "carol@test.com"


def test_buscar_usuario_inexistente(session):
	assert buscar_usuario_por_id(session, 99999) is None


def test_buscar_usuario_por_email(session):
	criado = criar_usuario(session, _payload("Dave", "dave@test.com"))
	achado = buscar_usuario_por_email(session, "dave@test.com")
	assert achado is not None
	assert achado.id == criado.id


def test_atualizar_usuario(session):
	criado = criar_usuario(session, _payload("Eve", "eve@test.com", admin=False))
	# Atualiza nome e admin; UsuarioBase exige campos obrigatórios -> reusa email/senha existentes
	atualizado = atualizar_usuario(
		session,
		criado.id,
		UsuarioBase(
			nome="Eve Atualizada",
			email=criado.email,
			senha="Senha1!",
			admin=True,
			carreira_id=None,
			curso_id=None,
		),
	)
	assert atualizado is not None
	assert atualizado.id == criado.id
	assert atualizado.nome == "Eve Atualizada"
	assert atualizado.admin is True


def test_atualizar_senha(session):
	criado = criar_usuario(session, _payload("Frank", "frank@test.com", senha="Senha1!"))
	novo = atualizar_senha(session, criado.id, "NovaSenha1!")
	assert novo is not None
	assert novo.id == criado.id
	assert novo.senha == "NovaSenha1!"


def test_deletar_usuario(session):
	criado = criar_usuario(session, _payload("Grace", "grace@test.com"))
	deletado = deletar_usuario(session, criado.id)
	assert deletado is not None
	assert deletado.id == criado.id
	assert buscar_usuario_por_id(session, criado.id) is None


def test_criar_usuario_email_duplicado(session):
	criar_usuario(session, _payload("Henry", "henry@test.com"))
	with pytest.raises(IntegrityError):
		criar_usuario(session, _payload("Harry", "henry@test.com"))
	session.rollback()


def test_criar_usuario_email_invalido():
	with pytest.raises(ValueError):
		_payload("Ivy", "ivyinvalido", "Senha1!")


def test_criar_usuario_senha_invalida():
	# Sem maiúscula e sem especial
	with pytest.raises(ValueError):
		_payload("Jack", "jack@test.com", "senha")

