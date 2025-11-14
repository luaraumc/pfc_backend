import importlib
import sys

import pytest


def test_main_configures_cors_and_includes_routers_with_fake_fastapi(monkeypatch):
	"""Verifica CORS e inclusão de routers usando uma Fake FastAPI."""
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

	import fastapi
	monkeypatch.setattr(fastapi, "FastAPI", FakeApp)

	sys.modules.pop("app.main", None)
	main = importlib.import_module("app.main")

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

	assert len(calls["routers"]) == 9


def test_main_app_has_cors_middleware(monkeypatch):
	"""Valida cabeçalhos CORS da app real para origem permitida e negada."""
	monkeypatch.setenv("KEY_CRYPT", "k")
	monkeypatch.setenv("ALGORITHM", "HS256")
	monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
	monkeypatch.setenv("DB_USER", "u")
	monkeypatch.setenv("DB_PASSWORD", "p")
	monkeypatch.setenv("DB_HOST", "localhost")
	monkeypatch.setenv("DB_PORT", "5432")
	monkeypatch.setenv("DB_NAME", "db")

	sys.modules.pop("app.main", None)
	main = importlib.import_module("app.main")

	from fastapi import FastAPI
	from fastapi.testclient import TestClient

	assert isinstance(main.app, FastAPI)

	client = TestClient(main.app)

	r = client.options(
		"/__qualquer__",
		headers={
			"Origin": "http://localhost:5173",
			"Access-Control-Request-Method": "GET",
		},
	)
	assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
	assert r.headers.get("access-control-allow-methods")
	assert r.headers.get("access-control-allow-credentials") in ("true", "True")

	r2 = client.options(
		"/__qualquer__",
		headers={
			"Origin": "http://evil.local",
			"Access-Control-Request-Method": "GET",
		},
	)
	assert r2.headers.get("access-control-allow-origin") is None

