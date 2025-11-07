import os
import sys
import importlib
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="module")
def app_client():
	# Configura variáveis de ambiente necessárias ANTES dos imports de app.*
	os.environ.setdefault("KEY_CRYPT", "secret")
	os.environ.setdefault("ALGORITHM", "HS256")
	os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
	# Evita falha ao importar app.dependencies (engine Postgres é criado, mas não usado nos testes)
	os.environ.setdefault("DB_USER", "u")
	os.environ.setdefault("DB_PASSWORD", "p")
	os.environ.setdefault("DB_HOST", "localhost")
	os.environ.setdefault("DB_PORT", "5432")
	os.environ.setdefault("DB_NAME", "db")

	# Reimport limpo de módulos que dependem de env
	sys.modules.pop("app.main", None)
	sys.modules.pop("app.models", None)
	sys.modules.pop("app.dependencies", None)

	# Importa modelos e Base
	from app.models import Base  # noqa: E402

	# Engine SQLite em memória compartilhada entre conexões
	engine = create_engine(
		"sqlite://",
		connect_args={"check_same_thread": False},
		poolclass=StaticPool,
	)
	# Habilita FKs para suportar ondelete
	event.listen(engine, "connect", lambda dbapi_conn, _: dbapi_conn.execute("PRAGMA foreign_keys=ON"))

	TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	Base.metadata.create_all(bind=engine)

	# Carrega app após preparar banco
	from app.main import app
	from app.dependencies import pegar_sessao

	# Override de sessão para usar SQLite
	def _override_session():
		db = TestingSessionLocal()
		try:
			yield db
		finally:
			db.close()

	app.dependency_overrides[pegar_sessao] = _override_session

	# Patch de envio de e-mail: captura códigos enviados
	captured_codes = []
	import app.routes.authRoutes as auth_mod

	def fake_send(dest, code):
		# Armazena código para uso nos testes; não envia nada
		captured_codes.append((dest, code))
		return {"id": "fake"}

	# Monkeypatch manual: substitui função usada na rota
	auth_mod.enviar_email = fake_send

	client = TestClient(app)

	try:
		yield client, TestingSessionLocal, captured_codes
	finally:
		# Limpa overrides e fecha banco
		app.dependency_overrides.clear()
		Base.metadata.drop_all(bind=engine)


def _seed_carreira_curso(SessionLocal):
	from app.models import Carreira, Curso
	db = SessionLocal()
	try:
		car = Carreira(nome="Dados", descricao="Desc")
		cur = Curso(nome="Ciência de Dados", descricao="Desc")
		db.add_all([car, cur])
		db.commit()
		db.refresh(car)
		db.refresh(cur)
		return car.id, cur.id
	finally:
		db.close()


def test_cadastro_sucesso_e_duplicado(app_client):
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

	# Duplicado
	r2 = client.post("/auth/cadastro", json=payload)
	assert r2.status_code == 400
	assert r2.json().get("detail") == "Email já cadastrado."


def test_cadastro_nao_admin_sem_carreira_ou_curso_erro(app_client):
	client, SessionLocal, _ = app_client
	# Sem carreira/curso
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
	client, SessionLocal, _ = app_client
	carreira_id, curso_id = _seed_carreira_curso(SessionLocal)

	# Garantir usuário existente via cadastro
	client.post("/auth/cadastro", json={
		"nome": "Beltrano",
		"email": "bel@empresa.com",
		"senha": "S3nh@Ok!",
		"admin": False,
		"carreira_id": carreira_id,
		"curso_id": curso_id,
	})

	# Login correto
	r = client.post("/auth/login", json={"email": "bel@empresa.com", "senha": "S3nh@Ok!"})
	assert r.status_code == 200
	body = r.json()
	assert body.get("token_type") == "Bearer"
	assert body.get("access_token")
	# Cookie de refresh deve estar setado no client
	assert client.cookies.get("refresh_token") is not None

	# Login incorreto
	r2 = client.post("/auth/login", json={"email": "bel@empresa.com", "senha": "errada"})
	assert r2.status_code == 400
	# Mensagem na rota possui ponto final
	assert r2.json().get("detail") == "E-mail ou senha incorretos."


def test_refresh_e_logout(app_client):
	client, SessionLocal, _ = app_client
	carreira_id, curso_id = _seed_carreira_curso(SessionLocal)

	# Cadastra e loga para obter refresh cookie
	client.post("/auth/cadastro", json={
		"nome": "Ciclana",
		"email": "cic@empresa.com",
		"senha": "S3nh@Ok!",
		"admin": False,
		"carreira_id": carreira_id,
		"curso_id": curso_id,
	})
	login_resp = client.post("/auth/login", json={"email": "cic@empresa.com", "senha": "S3nh@Ok!"})
	# Em ambiente de teste HTTP a cookie Secure pode não ser armazenada automaticamente pelo TestClient
	if client.cookies.get("refresh_token") is None:
		raw = login_resp.headers.get("set-cookie", "")
		if "refresh_token=" in raw:
			val = raw.split("refresh_token=", 1)[1].split(";", 1)[0]
			client.cookies.set("refresh_token", val)
	assert client.cookies.get("refresh_token") is not None

	# Usa refresh: envia cookie explicitamente para evitar problemas com flag Secure
	refresh_val = client.cookies.get("refresh_token")
	r = client.post("/auth/refresh", cookies={"refresh_token": refresh_val})
	assert r.status_code == 200
	data = r.json()
	assert data.get("access_token") and data.get("token_type") == "Bearer"

	# Logout remove cookie
	r2 = client.post("/auth/logout")
	assert r2.status_code == 200
	# Header Set-Cookie deve sinalizar remoção (valor vazio ou Max-Age=0)
	set_cookie = r2.headers.get("set-cookie", "")
	assert "refresh_token=" in set_cookie and ("Max-Age=0" in set_cookie or "Expires=" in set_cookie)


def test_recuperar_senha_fluxo_completo(app_client):
	client, SessionLocal, captured = app_client
	carreira_id, curso_id = _seed_carreira_curso(SessionLocal)

	email = "reset@empresa.com"
	# Cadastra usuário
	client.post("/auth/cadastro", json={
		"nome": "Reset",
		"email": email,
		"senha": "S3nh@Ok!",
		"admin": False,
		"carreira_id": carreira_id,
		"curso_id": curso_id,
	})

	# Solicita código (capturado pelo fake enviar_email)
	r = client.post("/auth/solicitar-codigo/recuperar-senha", json={"email": email})
	assert r.status_code == 200
	assert r.json().get("message") == "Código enviado para recuperação de senha."
	# Captura o último código enviado
	assert any(dest == email for dest, _ in captured)
	code = [c for dest, c in captured if dest == email][-1]

	# Confirma nova senha com o código recebido
	nova = "Nov@S3nh4!"
	r2 = client.post("/auth/recuperar-senha", json={
		"email": email,
		"codigo": code,
		"nova_senha": nova,
	})
	assert r2.status_code == 200
	assert r2.json().get("detail") == "Senha atualizada com sucesso."

	# Login com a nova senha deve funcionar
	r3 = client.post("/auth/login", json={"email": email, "senha": nova})
	assert r3.status_code == 200
	assert r3.json().get("access_token")

