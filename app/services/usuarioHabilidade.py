from app.models import UsuarioHabilidade # modelo de tabela definido no arquivo models.py
from app.schemas import UsuarioHabilidadeBase, UsuarioHabilidadeOut # schema de entrada e saída

"""
model_dump: converte um objeto do schema em um dicionário para criar ou atualizar modelos SQLAlchemy a partir dos dados recebidos
model_validate: converte um objeto em um schema Pydantic para retornar dados das funções CRUD no formato esperado pela API
exclude_unset: gera um dicionário para atualizar apenas os campos que foram informados, sem sobrescrever os demais
"""

# ======================= CRUD =======================

# CREATE / POST - Cria uma nova relação entre usuário e habilidade
def criar_usuario_habilidade(session, usuario_habilidade_data: UsuarioHabilidadeBase) -> UsuarioHabilidadeOut:
    novo_usuario_habilidade = UsuarioHabilidade(**usuario_habilidade_data.model_dump()) # Cria um objeto UsuarioHabilidade a partir dos dados do schema
    session.add(novo_usuario_habilidade)  # Adiciona no banco
    session.commit() # Salva no banco
    session.refresh(novo_usuario_habilidade) # Atualiza o objeto com dados do banco
    return UsuarioHabilidadeOut.model_validate(novo_usuario_habilidade) # Converte o modelo SQLAlchemy para o schema de saída (UsuarioHabilidadeOut)

# READ / GET - Lista todas as habilidades do usuário
def listar_habilidades_usuario(session, usuario_id: int) -> list[UsuarioHabilidadeOut]:
    habilidades = session.query(UsuarioHabilidade).filter_by(usuario_id=usuario_id).all()
    return [UsuarioHabilidadeOut.model_validate(habilidade) for habilidade in habilidades]

# DELETE / DELETE - Remove uma habilidade do usuário pelo id do usuário e da habilidade
def remover_usuario_habilidade(session, usuario_id: int, habilidade_id: int) -> UsuarioHabilidadeOut | None:
    usuario_habilidade = session.query(UsuarioHabilidade).filter_by(usuario_id=usuario_id, habilidade_id=habilidade_id).first()
    if usuario_habilidade:
        session.delete(usuario_habilidade)  # Remove do banco
        session.commit()
        return UsuarioHabilidadeOut.model_validate(usuario_habilidade) # Retorna a relação removida como schema de saída
    return None
