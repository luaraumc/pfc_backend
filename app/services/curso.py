from models import Curso, SessionLocal # modelo de tabela definido no arquivo models.py / sessões para executar operações
from models import setup_database # conexão do banco de dados

engine, SessionLocal, Base = setup_database()

# ======================= CRUD =======================

# CREATE - Cria um novo curso
def criar_curso(session, nome, descricao):
	novo_curso = Curso(nome=nome, descricao=descricao)
	session.add(novo_curso)
	session.commit()
	session.refresh(novo_curso)
	return novo_curso.id

# READ - Lista todos os cursos
def listar_cursos(session):
	return session.query(Curso).all()

# READ - Busca um curso pelo id
def buscar_curso_por_id(session, id):
	return session.query(Curso).filter(Curso.id == id).first()

# UPDATE - Atualiza os dados de um curso existente
def atualizar_curso(session, id, nome=None, descricao=None, atualizado_em=None):
	curso = session.query(Curso).filter(Curso.id == id).first()
	if curso:
		if nome:
			curso.nome = nome
		if descricao:
			curso.descricao = descricao
		if atualizado_em:
			curso.atualizado_em = atualizado_em
		session.commit()
	return curso

# DELETE - Remove um curso pelo id
def deletar_curso(session, id):
	curso = session.query(Curso).filter(Curso.id == id).first()
	if curso:
		session.delete(curso)
		session.commit()
	return curso
