"""
Testes do módulo app.main

Este arquivo garante que a aplicação FastAPI está configurada corretamente:

- test_main_configures_cors_and_includes_routers_with_fake_fastapi:
	Substitui FastAPI por uma fake app para inspecionar chamadas. Verifica se o
	middleware de CORS (CORSMiddleware) é registrado com os parâmetros esperados
	(allow_origins para http://localhost:5173 e http://127.0.0.1:5173, métodos/headers
	liberados e credenciais habilitadas) e se todos os routers são incluídos (9 chamadas).

- test_main_app_has_cors_middleware:
	Usa a app real com TestClient para validar o comportamento do CORS em uma
	requisição preflight (OPTIONS). Checa que uma origem permitida recebe os
	cabeçalhos adequados (allow-origin, allow-methods, allow-credentials) e que
	uma origem não permitida não recebe o cabeçalho allow-origin.
"""

import importlib
import sys

import pytest


def test_main_configures_cors_and_includes_routers_with_fake_fastapi(monkeypatch):
	# Preparar envs mínimos para evitar efeitos colaterais de imports em rotas
	monkeypatch.setenv("KEY_CRYPT", "k")
	monkeypatch.setenv("ALGORITHM", "HS256")
	monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
	monkeypatch.setenv("DB_USER", "u")
	monkeypatch.setenv("DB_PASSWORD", "p")
	monkeypatch.setenv("DB_HOST", "localhost")
	monkeypatch.setenv("DB_PORT", "5432")
	monkeypatch.setenv("DB_NAME", "db")

	calls = {"middleware": [], "routers": []}

	class FakeApp:
		__test__ = False

		def __init__(self, *args, **kwargs):
			pass

		def add_middleware(self, cls, **options):
			calls["middleware"].append((cls, options))

		def include_router(self, router):
			calls["routers"].append(router)

	# Substituir FastAPI por FakeApp antes do import de app.main
	import fastapi

	monkeypatch.setattr(fastapi, "FastAPI", FakeApp)

	# Reimportar módulo
	sys.modules.pop("app.main", None)
	main = importlib.import_module("app.main")

	# Verificações
	# 1) CORS configurado com os parâmetros esperados
	from fastapi.middleware.cors import CORSMiddleware

	cors_calls = [c for c in calls["middleware"] if c[0] is CORSMiddleware]
	assert len(cors_calls) == 1
	_, options = cors_calls[0]
	assert options["allow_origins"] == [
		"http://localhost:5173",
	]
	assert options["allow_credentials"] is True
	assert options["allow_methods"] == ["*"]
	assert options["allow_headers"] == ["*"]

	# 2) Routers incluídos (9 chamadas)
	assert len(calls["routers"]) == 9


def test_main_app_has_cors_middleware(monkeypatch):
	# Preparar envs mínimos pois as rotas podem importar dependências
	monkeypatch.setenv("KEY_CRYPT", "k")
	monkeypatch.setenv("ALGORITHM", "HS256")
	monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
	monkeypatch.setenv("DB_USER", "u")
	monkeypatch.setenv("DB_PASSWORD", "p")
	monkeypatch.setenv("DB_HOST", "localhost")
	monkeypatch.setenv("DB_PORT", "5432")
	monkeypatch.setenv("DB_NAME", "db")

	# Reimport limpo
	sys.modules.pop("app.main", None)
	main = importlib.import_module("app.main")

	# app é uma instância real de FastAPI
	from fastapi import FastAPI
	from fastapi.testclient import TestClient

	assert isinstance(main.app, FastAPI)

	client = TestClient(main.app)

	# Preflight request com origem permitida
	r = client.options(
		"/__qualquer__",
		headers={
			"Origin": "http://localhost:5173",
			"Access-Control-Request-Method": "GET",
		},
	)
	# Mesmo que rota não exista, cabeçalhos de CORS devem ser aplicados
	assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
	# allow-methods deve existir e conter algo ("*" ou lista)
	assert r.headers.get("access-control-allow-methods")
	# credenciais habilitadas
	assert r.headers.get("access-control-allow-credentials") in ("true", "True")

	# Origem não permitida não deve ecoar allow-origin
	r2 = client.options(
		"/__qualquer__",
		headers={
			"Origin": "http://evil.local",
			"Access-Control-Request-Method": "GET",
		},
	)
	assert r2.headers.get("access-control-allow-origin") is None

