import os
import sys

import pytest
from .utils_test_routes import (
	app_client_context,
	seed_carreira_curso,
	seed_usuario,
	criar_categoria,
	criar_habilidade,
	relacionar_carreira_habilidade,
	add_usuario_habilidade,
)


@pytest.fixture(scope="module")
def app_client():
	"""Fixture que fornece cliente de teste com autenticação sobrescrita e captura de e-mails."""
	with app_client_context(patch_email_modules=["app.routes.authRoutes"]) as (client, SessionLocal, captured):
		from app.main import app
		from app.dependencies import verificar_token

		app.dependency_overrides[verificar_token] = lambda: {"id": 1, "admin": True}

		try:
			yield client, SessionLocal, captured
		finally:
			app.dependency_overrides.pop(verificar_token, None)


def _seed_carreira_curso(SessionLocal):
	"""Cria carreira e curso padrões para os testes."""
	return seed_carreira_curso(SessionLocal)


def _seed_usuario(SessionLocal, nome="Fulano", email="f@e.com", senha="hash", carreira_id=None, curso_id=None, admin=False):
	"""Cria um usuário de teste com dados opcionais (carreira/curso/admin)."""
	return seed_usuario(SessionLocal, nome=nome, email=email, senha=senha, carreira_id=carreira_id, curso_id=curso_id, admin=admin)


def _seed_categoria_habilidade(SessionLocal, cat_nome="Backend", hab_nome="Python"):
	"""Cria uma categoria e uma habilidade associada para os testes."""
	cat_id = criar_categoria(SessionLocal, nome=cat_nome)
	hab_id = criar_habilidade(SessionLocal, nome=hab_nome, categoria_id=cat_id)
	return cat_id, hab_id


def _relacionar_carreira_habilidade(SessionLocal, carreira_id, habilidade_id, freq):
	"""Relaciona uma habilidade à carreira com a frequência informada."""
	relacionar_carreira_habilidade(SessionLocal, carreira_id, habilidade_id, freq)


def _add_usuario_habilidade(SessionLocal, usuario_id, habilidade_id):
	"""Associa uma habilidade ao usuário para os testes."""
	return add_usuario_habilidade(SessionLocal, usuario_id, habilidade_id)


def test_get_usuario_404_e_ok(app_client):
	"""Verifica 404 para usuário inexistente e 200 para usuário existente."""
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
	"""Garante atualização bem-sucedida e 404 ao tentar atualizar um ID inexistente."""
	client, SessionLocal, _ = app_client
	car_id, cur_id = _seed_carreira_curso(SessionLocal)
	uid = _seed_usuario(SessionLocal, nome="Antigo", carreira_id=car_id, curso_id=cur_id)

	r = client.put(f"/usuario/atualizar/{uid}", json={
		"nome": "Novo Nome",
		"carreira_id": car_id,
		"curso_id": cur_id,
	})
	assert r.status_code == 200
	assert r.json().get("message") == "Usuário atualizado com sucesso: Novo Nome"

	r2 = client.put("/usuario/atualizar/999999", json={
		"nome": "X",
		"carreira_id": car_id,
		"curso_id": cur_id,
	})
	assert r2.status_code == 404
	assert r2.json().get("detail") == "Usuário não encontrado"


def test_solicitar_codigo_atualizar_senha_e_atualizar(app_client):
	"""Solicita código por e-mail e atualiza a senha usando código válido."""
	client, SessionLocal, captured = app_client
	car_id, cur_id = _seed_carreira_curso(SessionLocal)
	email = "codigo@e.com"
	uid = _seed_usuario(SessionLocal, nome="Reset", email=email, carreira_id=car_id, curso_id=cur_id)

	r = client.post("/usuario/solicitar-codigo/atualizar-senha", json={"email": email})
	assert r.status_code == 200
	assert r.json().get("message") == "Código enviado para atualização de senha."

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
	"""Solicita código de exclusão e remove o usuário quando o motivo é válido."""
	client, SessionLocal, captured = app_client
	car_id, cur_id = _seed_carreira_curso(SessionLocal)
	email = "excluir@e.com"
	uid = _seed_usuario(SessionLocal, nome="Apagar", email=email, carreira_id=car_id, curso_id=cur_id)

	r = client.post("/usuario/solicitar-codigo/exclusao-conta", json={"email": email})
	assert r.status_code == 200
	assert r.json().get("message") == "Código enviado para exclusão de conta."

	code = [c for dest, c in captured if dest == email][-1]

	r_bad = client.delete(f"/usuario/deletar/{uid}", json={
		"email": email,
		"codigo": code,
		"motivo": "outra_coisa",
	})
	assert r_bad.status_code == 400
	assert r_bad.json().get("detail") == "Motivo inválido para exclusão"

	r2 = client.delete(f"/usuario/deletar/{uid}", json={
		"email": email,
		"codigo": code,
		"motivo": "exclusao_conta",
	})
	assert r2.status_code == 200
	assert r2.json().get("message") == "Usuário deletado com sucesso e registrado em auditoria."

	r3 = client.get(f"/usuario/{uid}")
	assert r3.status_code == 404


def test_listar_habilidades_usuario_e_faltantes(app_client):
	"""Lista habilidades do usuário e retorna as faltantes conforme a carreira definida."""
	client, SessionLocal, _ = app_client
	car_id, cur_id = _seed_carreira_curso(SessionLocal)
	uid_sem_carreira = _seed_usuario(SessionLocal, nome="SemCarreira", email="s@e.com")

	r0 = client.get(f"/usuario/{uid_sem_carreira}/habilidades-faltantes")
	assert r0.status_code == 400
	assert r0.json().get("detail") == "Usuário não possui carreira definida"

	uid = _seed_usuario(SessionLocal, nome="ComCarreira", email="c@e.com", carreira_id=car_id, curso_id=cur_id)
	cat1, hab1 = _seed_categoria_habilidade(SessionLocal, "Backend", "Python")
	cat2, hab2 = _seed_categoria_habilidade(SessionLocal, "Dados", "Pandas")

	_relacionar_carreira_habilidade(SessionLocal, car_id, hab1, 5)
	_relacionar_carreira_habilidade(SessionLocal, car_id, hab2, 1)

	_add_usuario_habilidade(SessionLocal, uid, hab1)

	r1 = client.get(f"/usuario/{uid}/habilidades")
	assert r1.status_code == 200
	assert isinstance(r1.json(), list) and len(r1.json()) == 1

	r2 = client.get(f"/usuario/{uid}/habilidades-faltantes")
	assert r2.status_code == 200
	lista = r2.json()
	assert isinstance(lista, list) and len(lista) == 1
	assert lista[0]["id"] == hab2 and lista[0]["frequencia"] == 1


def test_compatibilidades_monkeypatched(app_client, monkeypatch):
	"""Simula serviços de compatibilidade via monkeypatch e valida os endpoints de compatibilidade."""
	client, SessionLocal, _ = app_client
	car_id, cur_id = _seed_carreira_curso(SessionLocal)
	uid = _seed_usuario(SessionLocal, nome="Compat", email="k@e.com", carreira_id=car_id, curso_id=cur_id)

	import app.services.compatibilidade as comp

	def fake_top(session, usuario_id):
		"""Retorna lista simulada de carreiras com score para o usuário."""
		return [{"carreira_id": car_id, "score": 0.7}]

	def fake_one(session, usuario_id, carreira_id):
		"""Retorna compatibilidade simulada entre um usuário e uma carreira específica."""
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
	"""Adiciona habilidade a um usuário, trata duplicidade e remove a relação posteriormente."""
	client, SessionLocal, _ = app_client
	car_id, cur_id = _seed_carreira_curso(SessionLocal)
	uid = _seed_usuario(SessionLocal, nome="HabUser", email="h@e.com", carreira_id=car_id, curso_id=cur_id)
	_, hab_id = _seed_categoria_habilidade(SessionLocal, "Mobile", "Flutter")

	r1 = client.post(f"/usuario/{uid}/adicionar-habilidade/{hab_id}")
	assert r1.status_code == 200
	body = r1.json()
	assert body.get("usuario_id") == uid and body.get("habilidade_id") == hab_id

	r_dup = client.post(f"/usuario/{uid}/adicionar-habilidade/{hab_id}")
	assert r_dup.status_code == 400
	assert r_dup.json().get("detail") == "Habilidade já adicionada ao usuário"

	r2 = client.delete(f"/usuario/{uid}/remover-habilidade/{hab_id}")
	assert r2.status_code == 200
	body2 = r2.json()
	assert body2.get("usuario_id") == uid and body2.get("habilidade_id") == hab_id

	r3 = client.delete(f"/usuario/{uid}/remover-habilidade/{hab_id}")
	assert r3.status_code == 404
	assert r3.json().get("detail") == "Relação usuário-habilidade não encontrada"

