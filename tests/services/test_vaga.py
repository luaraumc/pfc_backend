import os
from datetime import datetime, timedelta

# === Env vars mínimas para evitar erros em imports (config/dependencies) ===
os.environ.setdefault("KEY_CRYPT", "test-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("DB_USER", "u")
os.environ.setdefault("DB_PASSWORD", "p")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "db")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import (
	Base,
	Carreira,
	Categoria,
	Habilidade,
	Vaga,
	VagaHabilidade,
	CarreiraHabilidade,
)
from app.schemas import VagaBase
from app.services import vaga as vaga_service
from app.services.extracao import padronizar_descricao


@pytest.fixture()
def session():
	engine = create_engine("sqlite+pysqlite:///:memory:")
	TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	Base.metadata.create_all(bind=engine)
	db = TestingSessionLocal()
	try:
		yield db
	finally:
		db.close()
		Base.metadata.drop_all(bind=engine)


# Helpers
def criar_categoria(session, nome: str) -> Categoria:
	cat = Categoria(nome=nome)
	session.add(cat)
	session.commit()
	session.refresh(cat)
	return cat


def criar_carreira(session, nome: str = "Dev", descricao: str = "desc") -> Carreira:
	c = Carreira(nome=nome, descricao=descricao)
	session.add(c)
	session.commit()
	session.refresh(c)
	return c


def criar_habilidade(session, nome: str, categoria_id: int) -> Habilidade:
	h = Habilidade(nome=nome, categoria_id=categoria_id)
	session.add(h)
	session.commit()
	session.refresh(h)
	return h


def criar_vaga_raw(session, titulo: str, descricao: str, carreira_id: int | None = None) -> Vaga:
	v = Vaga(titulo=titulo, descricao=descricao, carreira_id=carreira_id)
	session.add(v)
	session.commit()
	session.refresh(v)
	return v


# ======================= TESTES =======================


def test_criar_vaga_padroniza_descricao(session):
	carreira = criar_carreira(session, "Backend")
	raw_desc = "  Desenvolvedor  Sênior .NET 6  "
	expected = padronizar_descricao(raw_desc)

	data = VagaBase(titulo="Dev Sr .NET", descricao=raw_desc, carreira_id=carreira.id)
	out = vaga_service.criar_vaga(session, data)

	assert out.id > 0
	assert out.titulo == "Dev Sr .NET"
	assert out.carreira_id == carreira.id
	assert out.carreira_nome == carreira.nome
	assert out.descricao == expected  # descrição padronizada pelo service


def test_criar_vaga_duplicate_descricao_gera_erro(session):
	carreira = criar_carreira(session, "Dados")
	raw_desc = "Cientista de Dados Senior"

	primeira = VagaBase(titulo="CD Sr", descricao=raw_desc, carreira_id=carreira.id)
	vaga_service.criar_vaga(session, primeira)

	segunda = VagaBase(titulo="Outra", descricao=raw_desc, carreira_id=carreira.id)
	with pytest.raises(ValueError) as exc:
		vaga_service.criar_vaga(session, segunda)
	assert str(exc.value) == "DUPLICATE_VAGA_DESCRICAO"


def test_listar_vagas_ordem_desc_e_carreira_nome(session):
	carreira = criar_carreira(session, "Frontend")
	v1 = vaga_service.criar_vaga(session, VagaBase(titulo="A", descricao="desc a", carreira_id=carreira.id))
	v2 = vaga_service.criar_vaga(session, VagaBase(titulo="B", descricao="desc b", carreira_id=carreira.id))

	# Força v1 a ser bem antigo para garantir ordenação por criado_em desc
	v1_db = session.query(Vaga).filter(Vaga.id == v1.id).first()
	v1_db.criado_em = datetime(2000, 1, 1)
	session.commit()

	itens = vaga_service.listar_vagas(session)
	assert [i.id for i in itens][0] == v2.id
	assert all(i.carreira_nome == carreira.nome for i in itens)


def test_confirmar_habilidades_vaga_cria_atualiza_relaciona(session):
	cat_backend = criar_categoria(session, "Backend")
	cat_frontend = criar_categoria(session, "Frontend")
	carreira = criar_carreira(session, "Fullstack")
	# existentes
	hab_python = criar_habilidade(session, "Python", cat_backend.id)
	hab_node = criar_habilidade(session, "Node.js", cat_backend.id)
	# vaga
	vaga_out = vaga_service.criar_vaga(
		session,
		VagaBase(titulo="Dev FS", descricao="Stack variada", carreira_id=carreira.id),
	)

	# confirma com: criar React (categoria sugerida), atualizar Python (categoria para Frontend), renomear Node.js para NodeJS
	habilidades_finais = [
		{"nome": "React", "categoria_sugerida": "Frontend"},
		{"habilidade_id": hab_python.id, "nome": "Python", "categoria_id": cat_frontend.id},
		{"habilidade_id": hab_node.id, "nome": "NodeJS"},
		{"nome": "react"},  # duplicada por nome editado
	]

	resp = vaga_service.confirmar_habilidades_vaga(session, vaga_out.id, habilidades_finais)

	# Retorno básico da vaga
	assert resp["id"] == vaga_out.id
	assert resp["carreira_id"] == carreira.id
	assert set(resp["habilidades_criadas"]) == {"React"}
	assert set(resp["habilidades_ja_existiam"]) == {"Python", "NodeJS"}

	# Verifica renomeio de Node.js -> NodeJS e mudança de categoria de Python
	node_atual = session.query(Habilidade).filter(Habilidade.id == hab_node.id).first()
	assert node_atual.nome == "NodeJS"
	py_atual = session.query(Habilidade).filter(Habilidade.id == hab_python.id).first()
	assert py_atual.categoria_id == cat_frontend.id

	# Relações VagaHabilidade criadas (3 únicas)
	rels_vh = session.query(VagaHabilidade).filter(VagaHabilidade.vaga_id == vaga_out.id).all()
	assert len(rels_vh) == 3

	# Relações CarreiraHabilidade com frequência 1 para cada
	rels_ch = session.query(CarreiraHabilidade).filter(CarreiraHabilidade.carreira_id == carreira.id).all()
	assert len(rels_ch) == 3
	assert all((r.frequencia or 0) == 1 for r in rels_ch)


def test_confirmar_habilidades_vaga_categoria_pendente_created(session):
	carreira = criar_carreira(session, "Data")
	vaga_out = vaga_service.criar_vaga(session, VagaBase(titulo="Data Eng", descricao="Spark e coisas", carreira_id=carreira.id))

	resp = vaga_service.confirmar_habilidades_vaga(session, vaga_out.id, [
		{"nome": "TechFoo", "categoria_sugerida": "NaoExiste"}
	])

	# Deve ter criado a categoria 'categoria pendente' e a habilidade nela
	cat_pendente = session.query(Categoria).filter(Categoria.nome.ilike("categoria pendente")).first()
	assert cat_pendente is not None
	hab = session.query(Habilidade).filter(Habilidade.nome.ilike("TechFoo")).first()
	assert hab is not None and hab.categoria_id == cat_pendente.id


def test_confirmar_habilidades_vaga_inexistente(session):
	with pytest.raises(ValueError):
		vaga_service.confirmar_habilidades_vaga(session, 9999, [])


def test_confirmar_habilidades_vaga_conflito_renomear(session):
	cat = criar_categoria(session, "Infra")
	carreira = criar_carreira(session)
	_ = vaga_service.criar_vaga(session, VagaBase(titulo="V1", descricao="d1", carreira_id=carreira.id))
	h1 = criar_habilidade(session, "Docker", cat.id)
	h2 = criar_habilidade(session, "Container", cat.id)

	with pytest.raises(ValueError):
		vaga_service.confirmar_habilidades_vaga(session, 1, [{"habilidade_id": h2.id, "nome": "Docker"}])


def test_remover_relacao_vaga_habilidade(session):
	carreira = criar_carreira(session)
	cat = criar_categoria(session, "Cloud")
	h = criar_habilidade(session, "AWS", cat.id)
	v = criar_vaga_raw(session, "DevOps", padronizar_descricao("DevOps AWS"), carreira.id)
	# cria relação
	rel = VagaHabilidade(vaga_id=v.id, habilidade_id=h.id)
	session.add(rel)
	session.commit()

	ok1 = vaga_service.remover_relacao_vaga_habilidade(session, v.id, h.id)
	ok2 = vaga_service.remover_relacao_vaga_habilidade(session, v.id, h.id)
	assert ok1 is True and ok2 is False


def test_excluir_vaga_decrementando_freqs(session):
	carreira = criar_carreira(session)
	cat = criar_categoria(session, "DevOps")
	a = criar_habilidade(session, "Docker", cat.id)
	b = criar_habilidade(session, "Kubernetes", cat.id)
	# carreira_habilidade com freq 2 e 1
	ch_a = CarreiraHabilidade(carreira_id=carreira.id, habilidade_id=a.id, frequencia=2)
	ch_b = CarreiraHabilidade(carreira_id=carreira.id, habilidade_id=b.id, frequencia=1)
	session.add_all([ch_a, ch_b])
	session.commit()

	# vaga com as duas habilidades
	v = criar_vaga_raw(session, "DevOps SRE", padronizar_descricao("Docker e Kubernetes"), carreira.id)
	session.add_all([
		VagaHabilidade(vaga_id=v.id, habilidade_id=a.id),
		VagaHabilidade(vaga_id=v.id, habilidade_id=b.id),
	])
	session.commit()

	ok = vaga_service.excluir_vaga_decrementando(session, v.id)
	assert ok is True

	# a deve ficar com 1, b deve ser removida
	ch_a_db = session.query(CarreiraHabilidade).filter_by(carreira_id=carreira.id, habilidade_id=a.id).first()
	ch_b_db = session.query(CarreiraHabilidade).filter_by(carreira_id=carreira.id, habilidade_id=b.id).first()
	assert ch_a_db and (ch_a_db.frequencia or 0) == 1
	assert ch_b_db is None

	# vaga removida
	assert session.query(Vaga).filter(Vaga.id == v.id).first() is None

	# inexistente
	assert vaga_service.excluir_vaga_decrementando(session, 9999) is False


def test_extrair_habilidades_vaga_preview(monkeypatch, session):
	# categorias e habilidade existente
	back = criar_categoria(session, "Backend")
	front = criar_categoria(session, "Frontend")
	py = criar_habilidade(session, "Python", back.id)
	v = vaga_service.criar_vaga(session, VagaBase(titulo="Dev", descricao="Python e React", carreira_id=None))

	# monkeypatch a função usada dentro do módulo vaga
	def fake_extrair(descricao: str, session=None):
		return [
			{"nome": "Python", "categoria_sugerida": "Backend"},
			{"nome": "React", "categoria_sugerida": "Frontend"},
			{"nome": "Python", "categoria_sugerida": "Backend"},
		]

	monkeypatch.setattr(vaga_service, "extrair_habilidades_descricao", fake_extrair)

	itens = vaga_service.extrair_habilidades_vaga(session, v.id)
	# deduplicado
	assert len(itens) == 2
	# cria mapa por nome para facilitar
	por_nome = {i["nome"]: i for i in itens}

	assert por_nome["Python"]["habilidade_id"] == py.id
	assert por_nome["Python"]["categoria_id"] == back.id
	assert por_nome["Python"]["categoria_nome"] == "Backend"
	assert por_nome["Python"]["categoria"] == "Backend"

	assert por_nome["React"]["habilidade_id"] in (None, "")
	# Deve associar sugestão a categoria existente
	assert por_nome["React"]["categoria_id"] == front.id
	assert por_nome["React"]["categoria_nome"] == "Frontend"


def test_extrair_habilidades_vaga_vaga_inexistente(session):
	assert vaga_service.extrair_habilidades_vaga(session, 9999) == []

