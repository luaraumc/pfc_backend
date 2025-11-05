import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
from app.models import Categoria, Habilidade as HabilidadeModel
from app.schemas import HabilidadeAtualizar
from app.services.habilidade import (
	listar_habilidades,
	buscar_habilidade_por_id,
	atualizar_habilidade,
	deletar_habilidade,
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
def cria_categoria(session, nome="Tecnologia") -> Categoria:
	cat = Categoria(nome=nome)
	session.add(cat)
	session.commit()
	session.refresh(cat)
	return cat


def cria_habilidade(session, nome: str, categoria_id: int) -> HabilidadeModel:
	hab = HabilidadeModel(nome=nome, categoria_id=categoria_id)
	session.add(hab)
	session.commit()
	session.refresh(hab)
	return hab


def test_listar_habilidades_vazio(session):
	itens = listar_habilidades(session)
	assert isinstance(itens, list)
	assert itens == []


def test_listar_habilidades_populado(session):
	cat = cria_categoria(session, "Dados")
	cria_habilidade(session, "Python", cat.id)
	cria_habilidade(session, "SQL", cat.id)

	itens = listar_habilidades(session)
	nomes = {i.nome for i in itens}
	assert len(itens) == 2
	assert {"Python", "SQL"}.issubset(nomes)
	# Categoria é lida via propriedade 'categoria' do modelo
	categorias = {i.categoria for i in itens}
	assert categorias == {"Dados"}


def test_buscar_habilidade_por_id(session):
	cat = cria_categoria(session, "Infra")
	hab = cria_habilidade(session, "Docker", cat.id)

	out = buscar_habilidade_por_id(session, hab.id)
	assert out is not None
	assert out.id == hab.id
	assert out.nome == "Docker"
	assert out.categoria_id == cat.id
	assert out.categoria == "Infra"


def test_buscar_habilidade_inexistente(session):
	assert buscar_habilidade_por_id(session, 9999) is None


def test_atualizar_habilidade_nome(session):
	cat = cria_categoria(session, "DevOps")
	hab = cria_habilidade(session, "Jenkins", cat.id)

	atualizado = atualizar_habilidade(session, hab.id, HabilidadeAtualizar(nome="Jenkins CI"))
	assert atualizado is not None
	assert atualizado.id == hab.id
	assert atualizado.nome == "Jenkins CI"
	assert atualizado.categoria_id == cat.id
	assert atualizado.categoria == "DevOps"


def test_atualizar_habilidade_nome_vazio_nao_altera(session):
	cat = cria_categoria(session, "Web")
	hab = cria_habilidade(session, "React", cat.id)
	# nome whitespace não deve alterar
	atualizado = atualizar_habilidade(session, hab.id, HabilidadeAtualizar(nome="   "))
	assert atualizado is not None
	assert atualizado.nome == "React"


def test_atualizar_habilidade_categoria_invalida(session):
	cat = cria_categoria(session, "Backend")
	hab = cria_habilidade(session, "FastAPI", cat.id)
	# categoria_id inexistente deve retornar None
	atualizado = atualizar_habilidade(session, hab.id, HabilidadeAtualizar(categoria_id=9999))
	assert atualizado is None


def test_atualizar_habilidade_categoria_valida(session):
	cat1 = cria_categoria(session, "Dados")
	cat2 = cria_categoria(session, "BI")
	hab = cria_habilidade(session, "Power BI", cat1.id)

	atualizado = atualizar_habilidade(session, hab.id, HabilidadeAtualizar(categoria_id=cat2.id))
	assert atualizado is not None
	assert atualizado.categoria_id == cat2.id
	assert atualizado.categoria == "BI"


def test_deletar_habilidade(session):
	cat = cria_categoria(session, "Segurança")
	hab = cria_habilidade(session, "Firewall", cat.id)

	deletado = deletar_habilidade(session, hab.id)
	assert deletado is not None
	assert deletado.id == hab.id
	# Deve manter leitura do nome da categoria no DTO retornado
	assert deletado.categoria == "Segurança"
	# E não existir mais no banco
	assert buscar_habilidade_por_id(session, hab.id) is None

