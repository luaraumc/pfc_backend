import os
import sys
import importlib
from datetime import datetime, timedelta

import pytest
from .utils_test_routes import (
	app_client_context,
	seed_carreira_curso,
)


@pytest.fixture(scope="module")
def app_client():
	"""Inicializa o TestClient e intercepta envios de e-mail para testes de auth."""
	with app_client_context(patch_email_modules=["app.routes.authRoutes"]) as ctx:
		yield ctx


def _seed_carreira_curso(SessionLocal):
	"""Semeia carreira e curso delegando ao utilitário compartilhado."""
	return seed_carreira_curso(SessionLocal)


def test_cadastro_sucesso_e_duplicado(app_client):
	"""Verifica cadastro bem-sucedido e erro ao repetir e-mail já cadastrado."""
	client, SessionLocal, _ = app_client
	carreira_id, curso_id = _seed_carreira_curso(SessionLocal)

	payload = {
		"nome": "Fulana",
		"email": "fulana@empresa.com",
		"senha": "S3nh@Ok!",
		"admin": False,
		"carreira_id": carreira_id,
		"curso_id": curso_id,
	}
	r = client.post("/auth/cadastro", json=payload)
	assert r.status_code == 200
	assert "Usuário cadastrado com sucesso! Redirecionando..." in r.json().get("message", "")

	r2 = client.post("/auth/cadastro", json=payload)
	assert r2.status_code == 400
	assert r2.json().get("detail") == "Email já cadastrado."


def test_cadastro_nao_admin_sem_carreira_ou_curso_erro(app_client):
	"""Garante erro quando não-admin tenta cadastro sem carreira definida."""
	client, SessionLocal, _ = app_client
	payload = {
		"nome": "SemRelacao",
		"email": "sem@empresa.com",
		"senha": "S3nh@Ok!",
		"admin": False,
		"carreira_id": None,
		"curso_id": None,
	}
	r = client.post("/auth/cadastro", json=payload)
	# Rota agora exige apenas Carreira obrigatória quando não admin
	assert r.status_code == 400
	assert r.json().get("detail") == "Carreira é obrigatória."


def test_login_ok_e_incorreto(app_client):
	"""Valida login correto, criação do refresh cookie e rejeição com senha errada."""
	client, SessionLocal, _ = app_client
	carreira_id, curso_id = _seed_carreira_curso(SessionLocal)

	client.post("/auth/cadastro", json={
		"nome": "Beltrano",
		"email": "bel@empresa.com",
		"senha": "S3nh@Ok!",
		"admin": False,
		"carreira_id": carreira_id,
		"curso_id": curso_id,
	})

	r = client.post("/auth/login", json={"email": "bel@empresa.com", "senha": "S3nh@Ok!"})
	assert r.status_code == 200
	body = r.json()
	assert body.get("token_type") == "Bearer"
	assert body.get("access_token")
	assert client.cookies.get("refresh_token") is not None

	r2 = client.post("/auth/login", json={"email": "bel@empresa.com", "senha": "errada"})
	assert r2.status_code == 400
	assert r2.json().get("detail") == "E-mail ou senha incorretos."


def test_refresh_e_logout(app_client):
	"""Testa refresh para novo access token e limpeza do cookie no logout."""
	client, SessionLocal, _ = app_client
	carreira_id, curso_id = _seed_carreira_curso(SessionLocal)

	client.post("/auth/cadastro", json={
		"nome": "Ciclana",
		"email": "cic@empresa.com",
		"senha": "S3nh@Ok!",
		"admin": False,
		"carreira_id": carreira_id,
		"curso_id": curso_id,
	})
	login_resp = client.post("/auth/login", json={"email": "cic@empresa.com", "senha": "S3nh@Ok!"})
	if client.cookies.get("refresh_token") is None:
		raw = login_resp.headers.get("set-cookie", "")
		if "refresh_token=" in raw:
			val = raw.split("refresh_token=", 1)[1].split(";", 1)[0]
			client.cookies.set("refresh_token", val)
	assert client.cookies.get("refresh_token") is not None

	refresh_val = client.cookies.get("refresh_token")
	r = client.post("/auth/refresh", cookies={"refresh_token": refresh_val})
	assert r.status_code == 200
	data = r.json()
	assert data.get("access_token") and data.get("token_type") == "Bearer"

	r2 = client.post("/auth/logout")
	assert r2.status_code == 200
	set_cookie = r2.headers.get("set-cookie", "")
	assert "refresh_token=" in set_cookie and ("Max-Age=0" in set_cookie or "Expires=" in set_cookie)


def test_recuperar_senha_fluxo_completo(app_client):
	"""Executa o fluxo completo de recuperação: solicitar código, redefinir e logar."""
	client, SessionLocal, captured = app_client
	carreira_id, curso_id = _seed_carreira_curso(SessionLocal)
	email = "reset@empresa.com"
	client.post("/auth/cadastro", json={
		"nome": "Reset",
		"email": email,
		"senha": "S3nh@Ok!",
		"admin": False,
		"carreira_id": carreira_id,
		"curso_id": curso_id,
	})
	r = client.post("/auth/solicitar-codigo/recuperar-senha", json={"email": email})
	assert r.status_code == 200
	assert r.json().get("message") == "Código enviado para recuperação de senha."
	assert any(dest == email for dest, _ in captured)
	code = [c for dest, c in captured if dest == email][-1]

	nova = "Nov@S3nh4!"
	r2 = client.post("/auth/recuperar-senha", json={
		"email": email,
		"codigo": code,
		"nova_senha": nova,
	})
	assert r2.status_code == 200
	assert r2.json().get("detail") == "Senha atualizada com sucesso."

	r3 = client.post("/auth/login", json={"email": email, "senha": nova})
	assert r3.status_code == 200
	assert r3.json().get("access_token")

