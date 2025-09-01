from app.models import Usuario # modelo de tabela definido no arquivo models.py
from app.dependencies import setup_database # conexão do banco de dados
from app.schemas import UsuarioBase, UsuarioOut # conexão do banco de dados

engine, SessionLocal, Base = setup_database()

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# CREATE - Cria um novo usuário
def criar_usuario(session, usuario_data: UsuarioBase) -> UsuarioOut:
    novo_usuario = Usuario(**usuario_data.model_dump()) # Cria um objeto Usuario a partir dos dados do schema
    session.add(novo_usuario)  # Adiciona no banco
    session.commit() # Salva no banco
    session.refresh(novo_usuario) # Atualiza o objeto com dados do banco
    return UsuarioOut.model_validate(novo_usuario) # Converte o modelo SQLAlchemy para o schema de saída (UsuarioOut)

# READ - Lista todos os usuários
def listar_usuarios(session) -> list[UsuarioOut]:
    usuarios = session.query(Usuario).all()  # Busca todos os usuários no banco
    return [UsuarioOut.model_validate(usuario) for usuario in usuarios] # Converte cada usuário para o schema de saída

# READ - Busca um usuário pelo id
def buscar_usuario_por_id(session, id: int) -> UsuarioOut | None:
    usuario = session.query(Usuario).filter(Usuario.id == id).first()  # Busca o usuário pelo id
    return UsuarioOut.model_validate(usuario) if usuario else None # Se encontrado converte para schema de saída, senão retorna None

# UPDATE - Atualiza os dados de um usuário existente usando schema
def atualizar_usuario(session, id: int, usuario_data: UsuarioBase) -> UsuarioOut | None:
    usuario = session.query(Usuario).filter(Usuario.id == id).first()  # Busca o usuário pelo id
    if usuario:
        # Atualiza os campos do usuário com os dados recebidos
        for key, value in usuario_data.model_dump(exclude_unset=True).items():
            setattr(usuario, key, value)
        session.commit()
        session.refresh(usuario)
        return UsuarioOut.model_validate(usuario) # Retorna o usuário atualizado como schema de saída
    return None

# DELETE - Remove um usuário pelo id
def deletar_usuario(session, id: int) -> UsuarioOut | None:
    usuario = session.query(Usuario).filter(Usuario.id == id).first()  # Busca o usuário pelo id
    if usuario:
        session.delete(usuario)  # Remove do banco
        session.commit()
        return UsuarioOut.model_validate(usuario) # Retorna o usuário removido como schema de saída
    return None