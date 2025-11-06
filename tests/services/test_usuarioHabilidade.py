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
from app.models import Usuario, Habilidade, Categoria
from app.schemas import UsuarioHabilidadeBase, UsuarioHabilidadeOut
from app.services.usuarioHabilidade import (
	criar_usuario_habilidade,
	listar_habilidades_usuario,
	remover_usuario_habilidade,
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


# Helpers
def cria_usuario(session, nome: str, email: str, senha: str = "Senha1!") -> Usuario:
	u = Usuario(nome=nome, email=email, senha=senha)
	session.add(u)
	session.commit()
	session.refresh(u)
	return u


def cria_categoria(session, nome="Tecnologia") -> Categoria:
	cat = Categoria(nome=nome)
	session.add(cat)
	session.commit()
	session.refresh(cat)
	return cat


def cria_habilidade(session, nome: str, categoria_id: int) -> Habilidade:
	hab = Habilidade(nome=nome, categoria_id=categoria_id)
	session.add(hab)
	session.commit()
	session.refresh(hab)
	return hab


# =========================
# Testes
# =========================

def test_listar_habilidades_usuario_vazio(session):
	usuario = cria_usuario(session, "Alice", "alice@test.com")
	resultado = listar_habilidades_usuario(session, usuario.id)
	assert isinstance(resultado, list)
	assert resultado == []


def test_criar_usuario_habilidade(session):
	usuario = cria_usuario(session, "Bob", "bob@test.com")
	cat = cria_categoria(session)
	hab = cria_habilidade(session, "Python", cat.id)

	payload = UsuarioHabilidadeBase(usuario_id=usuario.id, habilidade_id=hab.id)
	out = criar_usuario_habilidade(session, payload)

	assert isinstance(out, UsuarioHabilidadeOut)
	assert out.id is not None
	assert out.usuario_id == usuario.id
	assert out.habilidade_id == hab.id


def test_listar_habilidades_usuario_populado(session):
	usuario = cria_usuario(session, "Carol", "carol@test.com")
	cat = cria_categoria(session)
	h1 = cria_habilidade(session, "Docker", cat.id)
	h2 = cria_habilidade(session, "Kubernetes", cat.id)

	criar_usuario_habilidade(session, UsuarioHabilidadeBase(usuario_id=usuario.id, habilidade_id=h1.id))
	criar_usuario_habilidade(session, UsuarioHabilidadeBase(usuario_id=usuario.id, habilidade_id=h2.id))

	resultado = listar_habilidades_usuario(session, usuario.id)
	assert len(resultado) == 2
	assert {h1.id, h2.id} == {r.habilidade_id for r in resultado}


def test_remover_usuario_habilidade(session):
	usuario = cria_usuario(session, "Dave", "dave@test.com")
	cat = cria_categoria(session)
	h = cria_habilidade(session, "Git", cat.id)
	criar_usuario_habilidade(session, UsuarioHabilidadeBase(usuario_id=usuario.id, habilidade_id=h.id))

	removida = remover_usuario_habilidade(session, usuario.id, h.id)
	assert removida is not None
	assert removida.usuario_id == usuario.id
	assert removida.habilidade_id == h.id

	assert listar_habilidades_usuario(session, usuario.id) == []


def test_remover_usuario_habilidade_inexistente(session):
	usuario = cria_usuario(session, "Eve", "eve@test.com")
	assert remover_usuario_habilidade(session, usuario.id, habilidade_id=9999) is None


def test_criar_usuario_habilidade_duplicada_gera_integrity_error(session):
	usuario = cria_usuario(session, "Frank", "frank@test.com")
	cat = cria_categoria(session)
	h = cria_habilidade(session, "SQL", cat.id)

	criar_usuario_habilidade(session, UsuarioHabilidadeBase(usuario_id=usuario.id, habilidade_id=h.id))

	with pytest.raises(IntegrityError):
		criar_usuario_habilidade(session, UsuarioHabilidadeBase(usuario_id=usuario.id, habilidade_id=h.id))
	session.rollback()

	resultado = listar_habilidades_usuario(session, usuario.id)
	assert len(resultado) == 1

