import os
import json
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
os.environ.setdefault("OPENAI_API_KEY", "test")

from app.dependencies import Base
from app.models import Normalizacao, Categoria
import app.services.extracao as extracao


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
def adiciona_categoria(session, nome: str) -> Categoria:
	c = Categoria(nome=nome)
	session.add(c)
	session.commit()
	session.refresh(c)
	return c


def adiciona_padrao(session, regex: str, padronizado: str) -> Normalizacao:
	n = Normalizacao(nome=regex, nome_padronizado=padronizado)
	session.add(n)
	session.commit()
	session.refresh(n)
	return n


def fake_openai_factory(payload):
	"""Retorna uma classe substituta de OpenAI que devolve payload ao chamar responses.create()."""
	class DummyClient:
		def __init__(self, api_key=None):
			# objeto simples com método create que retorna payload
			self.responses = type("Responses", (), {"create": lambda _self, **kwargs: payload})()

	return DummyClient


# =========================
# Testes de funções auxiliares
# =========================

def test_normalizar_habilidade_sem_db(session):
	assert extracao.normalizar_habilidade("  PyThOn 3.11  ", session=None) == "Python"
	# Pela implementação atual, ".NET 6" vira "Net 6" (não consolida para "Dotnet")
	assert extracao.normalizar_habilidade(".NET 6", session=None) == "Net 6"
	assert extracao.normalizar_habilidade("C# 10", session=None) == "C#"


def test_normalizar_habilidade_com_db(session):
	adiciona_padrao(session, r"^node(js)?$", "Node.js")
	adiciona_padrao(session, r"^kubernetes$", "Kubernetes")
	assert extracao.normalizar_habilidade("nodejs", session=session) == "Node.js"
	# com acento e caixa estranha deve normalizar antes do regex
	assert extracao.normalizar_habilidade("Kúbérnetes", session=session) == "Kubernetes"


def test_padronizar_descricao():
	entrada = "Desenvolvedor(a) BACKEND — APIs REST!"
	saida = extracao.padronizar_descricao(entrada)
	# Sem acentos, minúsculas, sem pontuação e com espaços normalizados
	assert saida == "desenvolvedora backend apis rest"


def test_deduplicar():
	k1 = extracao.deduplicar("Kubernetes")
	k2 = extracao.deduplicar("kuberNétès")
	assert k1 == k2


# =========================
# Testes de extrair_habilidades_descricao com OpenAI mockado
# =========================

def test_extrair_habilidades_output_text_json(monkeypatch, session):
	# categorias existentes no banco para validação case-insensitive
	adiciona_categoria(session, "Linguagens e formatos")
	adiciona_categoria(session, "DevOps")

	payload = type("Resp", (), {
		"output_text": json.dumps({
			"habilidades": [
				{"nome": "Python", "categoria": "Linguagens e formatos"},
				{"nome": "Docker", "categoria": "devops"},
			]
		})
	})()

	monkeypatch.setattr(extracao, "OpenAI", fake_openai_factory(payload))

	texto = "Vaga para dev com Python e Docker"
	itens = extracao.extrair_habilidades_descricao(texto, session=session)
	assert itens == [
		{"nome": "Python", "categoria_sugerida": "Linguagens e formatos"},
		{"nome": "Docker", "categoria_sugerida": "DevOps"},
	]


def test_extrair_habilidades_output_blocks(monkeypatch, session):
	adiciona_categoria(session, "Linguagens e formatos")
	bloco = type("Bloco", (), {"type": "output_text", "text": json.dumps({
		"habilidades": [
			{"nome": "Python", "categoria": "Linguagens e formatos"}
		]
	})})()
	payload = type("Resp", (), {"output": [bloco]})()

	monkeypatch.setattr(extracao, "OpenAI", fake_openai_factory(payload))

	itens = extracao.extrair_habilidades_descricao("qualquer", session=session)
	assert itens == [{"nome": "Python", "categoria_sugerida": "Linguagens e formatos"}]


def test_extrair_habilidades_json_embutido_e_dedup(monkeypatch, session):
	adiciona_categoria(session, "Linguagens e formatos")
	# Strings em vez de dicts, com duplicatas e versões
	json_embutido = json.dumps({
		"habilidades": ["Python", "python 3.10", "PYTHON"]
	})
	texto = f"Conteudo antes... {json_embutido} ...e depois"
	payload = type("Resp", (), {"output_text": texto})()

	monkeypatch.setattr(extracao, "OpenAI", fake_openai_factory(payload))

	itens = extracao.extrair_habilidades_descricao("vaga", session=session)
	# Apenas um Python, sem categoria sugerida
	assert itens == [{"nome": "Python", "categoria_sugerida": None}]


def test_extrair_habilidades_categoria_desconhecida(monkeypatch, session):
	# Sem adicionar categoria correspondente, deve vir None
	payload = type("Resp", (), {
		"output_text": json.dumps({
			"habilidades": [
				{"nome": "Kubernetes", "categoria": "Orquestracao"}
			]
		})
	})()

	monkeypatch.setattr(extracao, "OpenAI", fake_openai_factory(payload))
	itens = extracao.extrair_habilidades_descricao("texto", session=session)
	assert itens == [{"nome": "Kubernetes", "categoria_sugerida": None}]


def test_extrair_habilidades_quando_openai_falha(monkeypatch, session):
	class FailingClient:
		def __init__(self, api_key=None):
			class R:
				def create(self, **kwargs):
					raise RuntimeError("boom")
			self.responses = R()

	monkeypatch.setattr(extracao, "OpenAI", FailingClient)
	itens = extracao.extrair_habilidades_descricao("texto", session=session)
	assert itens == []

