import os
import pytest
from sqlalchemy.exc import IntegrityError

os.environ.setdefault("KEY_CRYPT", "test-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "testdb")

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
from tests.services.utils_test_services import session as session
from tests.services.utils_test_services import usuario_payload as _payload


def test_listar_usuarios_vazio(session):
	"""Garante lista vazia quando não há usuários cadastrados."""
	itens = listar_usuarios(session)
	assert isinstance(itens, list)
	assert itens == []


def test_criar_usuario(session):
	"""Cria um usuário padrão e valida os campos do retorno."""
	out = criar_usuario(session, _payload())
	assert isinstance(out, UsuarioOut)
	assert out.id is not None
	assert out.nome == "Usuário Teste"
	assert out.email == "user@test.com"
	assert out.admin is False


def test_listar_usuarios_populado(session):
	"""Lista usuários após dois cadastros e confere nomes."""
	criar_usuario(session, _payload("Alice", "alice@test.com"))
	criar_usuario(session, _payload("Bob", "bob@test.com"))
	itens = listar_usuarios(session)
	nomes = {i.nome for i in itens}
	assert len(itens) == 2
	assert {"Alice", "Bob"}.issubset(nomes)


def test_buscar_usuario_por_id(session):
	"""Busca usuário por ID e valida retorno."""
	criado = criar_usuario(session, _payload("Carol", "carol@test.com"))
	achado = buscar_usuario_por_id(session, criado.id)
	assert achado is not None
	assert achado.id == criado.id
	assert achado.email == "carol@test.com"


def test_buscar_usuario_inexistente(session):
	"""Retorna None ao buscar usuário inexistente."""
	assert buscar_usuario_por_id(session, 99999) is None


def test_buscar_usuario_por_email(session):
	"""Busca usuário por e-mail e confere ID correspondente."""
	criado = criar_usuario(session, _payload("Dave", "dave@test.com"))
	achado = buscar_usuario_por_email(session, "dave@test.com")
	assert achado is not None
	assert achado.id == criado.id


def test_atualizar_usuario(session):
	"""Atualiza nome e flag admin mantendo demais campos obrigatórios."""
	criado = criar_usuario(session, _payload("Eve", "eve@test.com", admin=False))
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
	"""Atualiza a senha do usuário mantendo o mesmo ID."""
	criado = criar_usuario(session, _payload("Frank", "frank@test.com", senha="Senha1!"))
	novo = atualizar_senha(session, criado.id, "NovaSenha1!")
	assert novo is not None
	assert novo.id == criado.id
	assert novo.senha == "NovaSenha1!"


def test_deletar_usuario(session):
	"""Deleta usuário e confirma que não é mais encontrado por ID."""
	criado = criar_usuario(session, _payload("Grace", "grace@test.com"))
	deletado = deletar_usuario(session, criado.id)
	assert deletado is not None
	assert deletado.id == criado.id
	assert buscar_usuario_por_id(session, criado.id) is None


def test_criar_usuario_email_duplicado(session):
	"""Criar com e-mail repetido deve gerar IntegrityError e rollback."""
	criar_usuario(session, _payload("Henry", "henry@test.com"))
	with pytest.raises(IntegrityError):
		criar_usuario(session, _payload("Harry", "henry@test.com"))
	session.rollback()


def test_criar_usuario_email_invalido():
	"""Criar payload com e-mail inválido deve levantar ValueError."""
	with pytest.raises(ValueError):
		_payload("Ivy", "ivyinvalido", "Senha1!")


def test_criar_usuario_senha_invalida():
	"""Criação com senha fraca (sem maiúscula/especial) deve falhar."""
	with pytest.raises(ValueError):
		_payload("Jack", "jack@test.com", "senha")

