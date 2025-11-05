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
from app.models import Carreira, Habilidade, Categoria
from app.schemas import CarreiraHabilidadeBase, CarreiraHabilidadeOut
from app.services.carreiraHabilidade import (
	criar_carreira_habilidade,
	listar_carreira_habilidades,
	remover_carreira_habilidade,
)


# =========================
# Fixture de sessão (SQLite em memória)
# =========================

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


# =========================
# Helpers para dados de apoio (FKs)
# =========================

def cria_categoria(session, nome="Tecnologia") -> Categoria:
	cat = Categoria(nome=nome)
	session.add(cat)
	session.commit()
	session.refresh(cat)
	return cat


def cria_carreira(session, nome="Backend", descricao="APIs e serviços") -> Carreira:
	car = Carreira(nome=nome, descricao=descricao)
	session.add(car)
	session.commit()
	session.refresh(car)
	return car


def cria_habilidade(session, nome: str, categoria_id: int) -> Habilidade:
	hab = Habilidade(nome=nome, categoria_id=categoria_id)
	session.add(hab)
	session.commit()
	session.refresh(hab)
	return hab


# =========================
# Testes
# =========================

def test_listar_carreira_habilidades_vazio(session):
	carreira = cria_carreira(session)
	resultado = listar_carreira_habilidades(session, carreira.id)
	assert isinstance(resultado, list)
	assert len(resultado) == 0


def test_criar_carreira_habilidade(session):
	cat = cria_categoria(session)
	carreira = cria_carreira(session)
	habilidade = cria_habilidade(session, nome="Python", categoria_id=cat.id)

	payload = CarreiraHabilidadeBase(
		carreira_id=carreira.id,
		habilidade_id=habilidade.id,
		frequencia=7,
	)
	out = criar_carreira_habilidade(session, payload)

	assert isinstance(out, CarreiraHabilidadeOut)
	assert out.id is not None
	assert out.carreira_id == carreira.id
	assert out.habilidade_id == habilidade.id
	assert out.frequencia == 7


def test_listar_carreira_habilidades_populado(session):
	cat = cria_categoria(session)
	carreira = cria_carreira(session)
	hab1 = cria_habilidade(session, nome="Python", categoria_id=cat.id)
	hab2 = cria_habilidade(session, nome="SQL", categoria_id=cat.id)

	criar_carreira_habilidade(session, CarreiraHabilidadeBase(carreira_id=carreira.id, habilidade_id=hab1.id, frequencia=3))
	criar_carreira_habilidade(session, CarreiraHabilidadeBase(carreira_id=carreira.id, habilidade_id=hab2.id, frequencia=5))

	resultado = listar_carreira_habilidades(session, carreira.id)
	assert len(resultado) == 2
	assert {hab1.id, hab2.id} == {r.habilidade_id for r in resultado}


def test_remover_carreira_habilidade(session):
	cat = cria_categoria(session)
	carreira = cria_carreira(session)
	hab = cria_habilidade(session, nome="Docker", categoria_id=cat.id)
	criar_carreira_habilidade(session, CarreiraHabilidadeBase(carreira_id=carreira.id, habilidade_id=hab.id, frequencia=1))

	removida = remover_carreira_habilidade(session, carreira.id, hab.id)
	assert removida is not None
	assert removida.carreira_id == carreira.id
	assert removida.habilidade_id == hab.id

	# Garante que não existe mais
	assert listar_carreira_habilidades(session, carreira.id) == []


def test_remover_carreira_habilidade_inexistente(session):
	carreira = cria_carreira(session)
	# habilidade/carregoria não são necessárias para tentar remover algo que não existe
	assert remover_carreira_habilidade(session, carreira.id, habilidade_id=9999) is None


def test_criar_carreira_habilidade_duplicada_gera_integrity_error(session):
	cat = cria_categoria(session)
	carreira = cria_carreira(session)
	hab = cria_habilidade(session, nome="Git", categoria_id=cat.id)

	criar_carreira_habilidade(session, CarreiraHabilidadeBase(carreira_id=carreira.id, habilidade_id=hab.id, frequencia=2))

	with pytest.raises(IntegrityError):
		criar_carreira_habilidade(session, CarreiraHabilidadeBase(carreira_id=carreira.id, habilidade_id=hab.id, frequencia=9))
	# rollback explícito para continuar usando a sessão após a exceção
	session.rollback()

	resultado = listar_carreira_habilidades(session, carreira.id)
	assert len(resultado) == 1
