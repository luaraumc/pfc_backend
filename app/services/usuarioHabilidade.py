from app.models.usuarioHabilidadeModels import UsuarioHabilidade # modelo de tabela
from app.schemas.usuarioHabilidadeSchemas import UsuarioHabilidadeBase, UsuarioHabilidadeOut # schema de entrada e saída

def criar_usuario_habilidade(session, usuario_habilidade_data: UsuarioHabilidadeBase) -> UsuarioHabilidadeOut:
    """Cria uma nova associação entre usuário e habilidade no banco de dados e retorna como UsuarioHabilidadeOut"""
    novo_usuario_habilidade = UsuarioHabilidade(**usuario_habilidade_data.model_dump())
    session.add(novo_usuario_habilidade)
    session.commit()
    session.refresh(novo_usuario_habilidade)
    return UsuarioHabilidadeOut.model_validate(novo_usuario_habilidade)

def listar_habilidades_usuario(session, usuario_id: int) -> list[UsuarioHabilidadeOut]:
    """Lista todas as habilidades associadas a um usuário específico e retorna como lista de UsuarioHabilidadeOut"""
    habilidades = session.query(UsuarioHabilidade).filter_by(usuario_id=usuario_id).all()
    return [UsuarioHabilidadeOut.model_validate(habilidade) for habilidade in habilidades]

def remover_usuario_habilidade(session, usuario_id: int, habilidade_id: int) -> UsuarioHabilidadeOut | None:
    """Remove a associação entre um usuário e uma habilidade específica e retorna os dados removidos ou None se não encontrada"""
    usuario_habilidade = session.query(UsuarioHabilidade).filter_by(usuario_id=usuario_id, habilidade_id=habilidade_id).first()
    if usuario_habilidade:
        session.delete(usuario_habilidade)
        session.commit()
        return UsuarioHabilidadeOut.model_validate(usuario_habilidade)
    return None
