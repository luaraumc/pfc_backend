import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="module")
def app_client():
	# Env mínimos
	os.environ.setdefault("KEY_CRYPT", "k")
	os.environ.setdefault("ALGORITHM", "HS256")
	os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
	os.environ.setdefault("DB_USER", "u")
	os.environ.setdefault("DB_PASSWORD", "p")
	os.environ.setdefault("DB_HOST", "localhost")
	os.environ.setdefault("DB_PORT", "5432")
	os.environ.setdefault("DB_NAME", "db")

	# Reimport limpo
	for m in ("app.main", "app.models", "app.dependencies"):
		sys.modules.pop(m, None)

	from app.models import Base  # noqa: E402

	engine = create_engine(
		"sqlite://",
		connect_args={"check_same_thread": False},
		poolclass=StaticPool,
	)
	event.listen(engine, "connect", lambda dbapi_conn, _: dbapi_conn.execute("PRAGMA foreign_keys=ON"))
	TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
	Base.metadata.create_all(bind=engine)

	from app.main import app
	from app.dependencies import pegar_sessao, verificar_token

	# Override sessão
	def _override_session():
		db = TestingSessionLocal()
		try:
			yield db
		finally:
			db.close()

	app.dependency_overrides[pegar_sessao] = _override_session
	# Override auth
	app.dependency_overrides[verificar_token] = lambda: {"id": 1, "admin": True}

	# Patch envio de e-mail do módulo authRoutes para capturar códigos
	import app.routes.authRoutes as auth_mod
	captured = []

	def fake_send(dest, code):
		captured.append((dest, code))
		return {"id": "fake"}

	auth_mod.enviar_email = fake_send

	client = TestClient(app)
	try:
		yield client, TestingSessionLocal, captured
	finally:
		app.dependency_overrides.clear()
		Base.metadata.drop_all(bind=engine)


def _seed_carreira_curso(SessionLocal):
	from app.models import Carreira, Curso
	db = SessionLocal()
	try:
		car = Carreira(nome="Dados", descricao="d")
		cur = Curso(nome="ADS", descricao="c")
		db.add_all([car, cur]); db.commit(); db.refresh(car); db.refresh(cur)
		return car.id, cur.id
	finally:
		db.close()


def _seed_usuario(SessionLocal, nome="Fulano", email="f@e.com", senha="hash", carreira_id=None, curso_id=None, admin=False):
	from app.models import Usuario
	db = SessionLocal()
	try:
		u = Usuario(nome=nome, email=email, senha=senha, admin=admin, carreira_id=carreira_id, curso_id=curso_id)
		db.add(u); db.commit(); db.refresh(u)
		return u.id
	finally:
		db.close()


def _seed_categoria_habilidade(SessionLocal, cat_nome="Backend", hab_nome="Python"):
	from app.models import Categoria, Habilidade
	db = SessionLocal()
	try:
		cat = Categoria(nome=cat_nome)
		db.add(cat); db.commit(); db.refresh(cat)
		hab = Habilidade(nome=hab_nome, categoria_id=cat.id)
		db.add(hab); db.commit(); db.refresh(hab)
		return cat.id, hab.id
	finally:
		db.close()


def _relacionar_carreira_habilidade(SessionLocal, carreira_id, habilidade_id, freq):
	from app.models import CarreiraHabilidade
	db = SessionLocal()
	try:
		rel = CarreiraHabilidade(carreira_id=carreira_id, habilidade_id=habilidade_id, frequencia=freq)
		db.add(rel); db.commit(); db.refresh(rel)
	finally:
		db.close()


def _add_usuario_habilidade(SessionLocal, usuario_id, habilidade_id):
	from app.models import UsuarioHabilidade
	db = SessionLocal()
	try:
		rel = UsuarioHabilidade(usuario_id=usuario_id, habilidade_id=habilidade_id)
		db.add(rel); db.commit(); db.refresh(rel)
		return rel.id
	finally:
		db.close()


def test_get_usuario_404_e_ok(app_client):
	client, SessionLocal, _ = app_client
	car_id, cur_id = _seed_carreira_curso(SessionLocal)
	uid = _seed_usuario(SessionLocal, carreira_id=car_id, curso_id=cur_id)

	r1 = client.get("/usuario/999999")
	assert r1.status_code == 404
	assert r1.json().get("detail") == "Usuário não encontrado"

	r2 = client.get(f"/usuario/{uid}")
	assert r2.status_code == 200
	assert r2.json().get("id") == uid


def test_atualizar_usuario_sucesso_e_404(app_client):
	client, SessionLocal, _ = app_client
	car_id, cur_id = _seed_carreira_curso(SessionLocal)
	uid = _seed_usuario(SessionLocal, nome="Antigo", carreira_id=car_id, curso_id=cur_id)

	# Atualiza
	r = client.put(f"/usuario/atualizar/{uid}", json={
		"nome": "Novo Nome",
		"carreira_id": car_id,
		"curso_id": cur_id,
	})
	assert r.status_code == 200
	assert r.json().get("message") == "Usuário atualizado com sucesso: Novo Nome"

	# 404
	r2 = client.put("/usuario/atualizar/999999", json={
		"nome": "X",
		"carreira_id": car_id,
		"curso_id": cur_id,
	})
	assert r2.status_code == 404
	assert r2.json().get("detail") == "Usuário não encontrado"


def test_solicitar_codigo_atualizar_senha_e_atualizar(app_client):
	client, SessionLocal, captured = app_client
	car_id, cur_id = _seed_carreira_curso(SessionLocal)
	email = "codigo@e.com"
	uid = _seed_usuario(SessionLocal, nome="Reset", email=email, carreira_id=car_id, curso_id=cur_id)

	r = client.post("/usuario/solicitar-codigo/atualizar-senha", json={"email": email})
	assert r.status_code == 200
	assert r.json().get("message") == "Código enviado para atualização de senha."

	# Captura o último código enviado para o e-mail
	code = [c for dest, c in captured if dest == email][-1]

	nova = "Nov@S3nh4!"
	r2 = client.put(f"/usuario/atualizar-senha/{uid}", json={
		"email": email,
		"codigo": code,
		"nova_senha": nova,
	})
	assert r2.status_code == 200
	assert r2.json().get("message").startswith("Senha atualizada com sucesso para o usuário:")


def test_solicitar_codigo_exclusao_e_deletar_usuario(app_client):
	client, SessionLocal, captured = app_client
	car_id, cur_id = _seed_carreira_curso(SessionLocal)
	email = "excluir@e.com"
	uid = _seed_usuario(SessionLocal, nome="Apagar", email=email, carreira_id=car_id, curso_id=cur_id)

	r = client.post("/usuario/solicitar-codigo/exclusao-conta", json={"email": email})
	assert r.status_code == 200
	assert r.json().get("message") == "Código enviado para exclusão de conta."

	code = [c for dest, c in captured if dest == email][-1]

	# Motivo errado
	r_bad = client.delete(f"/usuario/deletar/{uid}", json={
		"email": email,
		"codigo": code,
		"motivo": "outra_coisa",
	})
	assert r_bad.status_code == 400
	assert r_bad.json().get("detail") == "Motivo inválido para exclusão"

	# Motivo correto
	r2 = client.delete(f"/usuario/deletar/{uid}", json={
		"email": email,
		"codigo": code,
		"motivo": "exclusao_conta",
	})
	assert r2.status_code == 200
	assert r2.json().get("message") == "Usuário deletado com sucesso e registrado em auditoria."

	# Agora deve retornar 404 ao buscar
	r3 = client.get(f"/usuario/{uid}")
	assert r3.status_code == 404


def test_listar_habilidades_usuario_e_faltantes(app_client):
	client, SessionLocal, _ = app_client
	car_id, cur_id = _seed_carreira_curso(SessionLocal)
	uid_sem_carreira = _seed_usuario(SessionLocal, nome="SemCarreira", email="s@e.com")

	# faltantes com usuário sem carreira -> 400
	r0 = client.get(f"/usuario/{uid_sem_carreira}/habilidades-faltantes")
	assert r0.status_code == 400
	assert r0.json().get("detail") == "Usuário não possui carreira definida"

	# Usuário com carreira
	uid = _seed_usuario(SessionLocal, nome="ComCarreira", email="c@e.com", carreira_id=car_id, curso_id=cur_id)
	cat1, hab1 = _seed_categoria_habilidade(SessionLocal, "Backend", "Python")
	cat2, hab2 = _seed_categoria_habilidade(SessionLocal, "Dados", "Pandas")

	# Frequências da carreira
	_relacionar_carreira_habilidade(SessionLocal, car_id, hab1, 5)
	_relacionar_carreira_habilidade(SessionLocal, car_id, hab2, 1)

	# Usuário possui hab1
	_add_usuario_habilidade(SessionLocal, uid, hab1)

	# Listar habilidades do usuário (deve ter 1)
	r1 = client.get(f"/usuario/{uid}/habilidades")
	assert r1.status_code == 200
	assert isinstance(r1.json(), list) and len(r1.json()) == 1

	# Faltantes (deve retornar somente hab2, com frequência 1)
	r2 = client.get(f"/usuario/{uid}/habilidades-faltantes")
	assert r2.status_code == 200
	lista = r2.json()
	assert isinstance(lista, list) and len(lista) == 1
	assert lista[0]["id"] == hab2 and lista[0]["frequencia"] == 1


def test_compatibilidades_monkeypatched(app_client, monkeypatch):
	client, SessionLocal, _ = app_client
	car_id, cur_id = _seed_carreira_curso(SessionLocal)
	uid = _seed_usuario(SessionLocal, nome="Compat", email="k@e.com", carreira_id=car_id, curso_id=cur_id)

	# Patch de serviços de compatibilidade
	import app.services.compatibilidade as comp

	def fake_top(session, usuario_id):
		return [{"carreira_id": car_id, "score": 0.7}]

	def fake_one(session, usuario_id, carreira_id):
		return {"usuario_id": usuario_id, "carreira_id": carreira_id, "score": 0.5}

	monkeypatch.setattr(comp, "compatibilidade_carreiras_por_usuario", fake_top)
	monkeypatch.setattr(comp, "calcular_compatibilidade_usuario_carreira", fake_one)

	r1 = client.get(f"/usuario/{uid}/compatibilidade/top")
	assert r1.status_code == 200
	assert r1.json() == [{"carreira_id": car_id, "score": 0.7}]

	r2 = client.get(f"/usuario/{uid}/compatibilidade/carreira/{car_id}")
	assert r2.status_code == 200
	assert r2.json() == {"usuario_id": uid, "carreira_id": car_id, "score": 0.5}


def test_adicionar_e_remover_habilidade_usuario(app_client):
	client, SessionLocal, _ = app_client
	car_id, cur_id = _seed_carreira_curso(SessionLocal)
	uid = _seed_usuario(SessionLocal, nome="HabUser", email="h@e.com", carreira_id=car_id, curso_id=cur_id)
	_, hab_id = _seed_categoria_habilidade(SessionLocal, "Mobile", "Flutter")

	# Adiciona
	r1 = client.post(f"/usuario/{uid}/adicionar-habilidade/{hab_id}")
	assert r1.status_code == 200
	body = r1.json()
	assert body.get("usuario_id") == uid and body.get("habilidade_id") == hab_id

	# Duplicado -> 400
	r_dup = client.post(f"/usuario/{uid}/adicionar-habilidade/{hab_id}")
	assert r_dup.status_code == 400
	assert r_dup.json().get("detail") == "Habilidade já adicionada ao usuário"

	# Remover
	r2 = client.delete(f"/usuario/{uid}/remover-habilidade/{hab_id}")
	assert r2.status_code == 200
	body2 = r2.json()
	assert body2.get("usuario_id") == uid and body2.get("habilidade_id") == hab_id

	# Remover inexistente -> 404
	r3 = client.delete(f"/usuario/{uid}/remover-habilidade/{hab_id}")
	assert r3.status_code == 404
	assert r3.json().get("detail") == "Relação usuário-habilidade não encontrada"

