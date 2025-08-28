from app.models import Usuario # modelo de tabela definido no arquivo models.py

# ======================= CRUD =======================

# CREATE - Cria um novo usuário
def criar_usuario(session, nome, email, senha, curso_id):
    novo_usuario = Usuario(nome=nome, email=email, senha=senha, curso_id=curso_id)
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)
    return novo_usuario.id

# READ - Lista todos os usuário
def listar_usuario(session):
    return session.query(Usuario).all()

# READ - Busca um usuário pelo id
def buscar_usuario_por_id(session, id):
    return session.query(Usuario).filter(Usuario.id == id).first()

# UPDATE - Atualiza os dados de um usuário existente
def atualizar_usuario(session, id, nome=None, email=None, senha=None, atualizado_em=None):
    usuario = session.query(Usuario).filter(Usuario.id == id).first()
    if usuario:
        if nome:
            usuario.nome = nome
        if email:
            usuario.email = email
        if senha:
            usuario.senha = senha
        if atualizado_em:
            usuario.atualizado_em = atualizado_em
        session.commit()
    return usuario

# DELETE - Remove um usuário pelo id
def deletar_usuario(session, id):
    usuario = session.query(Usuario).filter(Usuario.id == id).first()
    if usuario:
        session.delete(usuario)
        session.commit()
    return usuario