from app.models import UsuarioHabilidade # modelo de tabela definido no arquivo models.py
from app.dependencies import setup_database # conexão do banco de dados
from app.schemas import UsuarioHabilidadeBase, UsuarioHabilidadeOut # schema de entrada e saída


def criar_usuario_habilidade(session, usuario_habilidade_data: UsuarioHabilidadeBase) -> UsuarioHabilidadeOut:
    novo_usuario_habilidade = UsuarioHabilidade(**usuario_habilidade_data.model_dump()) # Cria um objeto Usuario a partir dos dados do schema
    session.add(novo_usuario_habilidade)  # Adiciona no banco
    session.commit() # Salva no banco
    session.refresh(novo_usuario_habilidade) # Atualiza o objeto com dados do banco
    return UsuarioHabilidadeOut.model_validate(novo_usuario_habilidade)