from app.models import Carreira # modelo de tabela definido no arquivo models.py

# ======================= CRUD =======================

# CREATE - Cria uma nova carreira
def criar_carreira(session, nome, descricao):
	nova_carreira = Carreira(nome=nome, descricao=descricao)
	session.add(nova_carreira)
	session.commit()
	session.refresh(nova_carreira)
	return nova_carreira.id

# READ - Lista todas as carreira
def listar_carreira(session):
	return session.query(Carreira).all()

# READ - Busca uma carreira pelo id
def buscar_carreira_por_id(session, id):
	return session.query(Carreira).filter(Carreira.id == id).first()

# UPDATE - Atualiza os dados de uma carreira existente
def atualizar_carreira(session, id, nome=None, descricao=None, atualizado_em=None):
	carreira = session.query(Carreira).filter(Carreira.id == id).first()
	if carreira:
		if nome:
			carreira.nome = nome
		if descricao:
			carreira.descricao = descricao
		if atualizado_em:
			carreira.atualizado_em = atualizado_em
		session.commit()
	return carreira

# DELETE - Remove uma carreira pelo id
def deletar_carreira(session, id):
	carreira = session.query(Carreira).filter(Carreira.id == id).first()
	if carreira:
		session.delete(carreira)
		session.commit()
	return carreira