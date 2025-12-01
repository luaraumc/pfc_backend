import os
import json
import pytest

os.environ.setdefault("KEY_CRYPT", "test-key")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("DB_USER", "user")
os.environ.setdefault("DB_PASSWORD", "pass")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "testdb")
os.environ.setdefault("OPENAI_API_KEY", "test")

from app.models import Normalizacao, Categoria
import app.services.extracao as extracao
from tests.services.utils_test_services import session as session
from tests.services.utils_test_services import (
	adiciona_padrao,
	cria_categoria as adiciona_categoria,
	fake_openai_factory,
)

def test_normalizar_habilidade_sem_db(session):
	"""Normaliza nomes de habilidades sem consultar o banco de dados."""
	assert extracao.normalizar_habilidade("  PyThOn 3.11  ", session=None) == "Python"
	assert extracao.normalizar_habilidade(".NET 6", session=None) == "Net 6"
	assert extracao.normalizar_habilidade("C# 10", session=None) == "C#"


def test_normalizar_habilidade_com_db(session):
	"""Aplica padrões de normalização vindos do banco (regex)."""
	adiciona_padrao(session, r"^node(js)?$", "Node.js")
	adiciona_padrao(session, r"^kubernetes$", "Kubernetes")
	assert extracao.normalizar_habilidade("nodejs", session=session) == "Node.js"
	assert extracao.normalizar_habilidade("Kúbérnetes", session=session) == "Kubernetes"


def test_padronizar_descricao():
	"""Padroniza descrição removendo acentos, pontuação e normalizando espaços."""
	entrada = "Desenvolvedor(a) BACKEND — APIs REST!"
	saida = extracao.padronizar_descricao(entrada)
	assert saida == "desenvolvedora backend apis rest"


def test_deduplicar():
	"""Gera chave de deduplicação idêntica para variações textuais iguais."""
	k1 = extracao.deduplicar("Kubernetes")
	k2 = extracao.deduplicar("kuberNétès")
	assert k1 == k2

def test_extrair_habilidades_output_text_json(monkeypatch, session):
	"""Processa output_text JSON do OpenAI e valida normalização e categorias."""
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
	"""Lê habilidades do atributo output (blocks) quando presente."""
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
	"""Extrai JSON embutido no texto, deduplica e remove versões."""
	adiciona_categoria(session, "Linguagens e formatos")
	json_embutido = json.dumps({
		"habilidades": ["Python", "python 3.10", "PYTHON"]
	})
	texto = f"Conteudo antes... {json_embutido} ...e depois"
	payload = type("Resp", (), {"output_text": texto})()

	monkeypatch.setattr(extracao, "OpenAI", fake_openai_factory(payload))

	itens = extracao.extrair_habilidades_descricao("vaga", session=session)
	assert itens == [{"nome": "Python", "categoria_sugerida": None}]


def test_extrair_habilidades_categoria_desconhecida(monkeypatch, session):
	"""Quando categoria sugerida não existe no banco, retorna None."""
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
	"""Retorna lista vazia quando cliente OpenAI lança exceção."""
	class FailingClient:
		def __init__(self, api_key=None):
			class R:
				def create(self, **kwargs):
					raise RuntimeError("boom")
			self.responses = R()

	monkeypatch.setattr(extracao, "OpenAI", FailingClient)
	itens = extracao.extrair_habilidades_descricao("texto", session=session)
	assert itens == []

