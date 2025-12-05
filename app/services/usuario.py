from app.models.usuarioModels import Usuario
from app.schemas.usuarioSchemas import UsuarioOut, UsuarioBase
from typing import Any, Mapping


def criar_usuario(session, usuario_data: Mapping[str, Any]) -> UsuarioOut:
    """Cria um novo usuário com dados mínimos (dict), salva e retorna como UsuarioOut."""
    novo_usuario = Usuario(**dict(usuario_data))
    session.add(novo_usuario)
    session.commit()
    session.refresh(novo_usuario)
    return UsuarioOut.model_validate(novo_usuario)


def listar_usuarios(session) -> list[UsuarioOut]:
    """Busca todos os usuários no banco de dados e retorna uma lista convertida para UsuarioOut"""
    usuarios = session.query(Usuario).all()
    return [UsuarioOut.model_validate(usuario) for usuario in usuarios]


def buscar_usuario_por_id(session, id: int) -> UsuarioOut | None:
    """Busca um usuário específico pelo ID no banco de dados e retorna como UsuarioOut ou None se não encontrado"""
    usuario = session.query(Usuario).filter(Usuario.id == id).first()
    return UsuarioOut.model_validate(usuario) if usuario else None


def buscar_usuario_por_email(session, email: str) -> UsuarioOut | None:
    """Busca um usuário específico pelo email no banco de dados e retorna como UsuarioOut ou None se não encontrado"""
    usuario = session.query(Usuario).filter(Usuario.email == email).first()
    return UsuarioOut.model_validate(usuario) if usuario else None


def atualizar_usuario(session, id: int, usuario_data: UsuarioBase) -> UsuarioOut | None:
    """Busca um usuário pelo ID, atualiza apenas os campos informados no schema, salva no banco e retorna como UsuarioOut"""
    usuario = session.query(Usuario).filter(Usuario.id == id).first()
    if usuario:
        for key, value in usuario_data.model_dump(exclude_unset=True).items():
            setattr(usuario, key, value)
        session.commit()
        session.refresh(usuario)
        return UsuarioOut.model_validate(usuario)
    return None


def atualizar_senha(session, id: int, nova_senha: str) -> UsuarioOut | None:
    """Busca um usuário pelo ID, atualiza apenas a senha, salva no banco e retorna como UsuarioOut"""
    usuario = session.query(Usuario).filter(Usuario.id == id).first()
    if usuario:
        usuario.senha = nova_senha
        session.commit()
        session.refresh(usuario)
        return UsuarioOut.model_validate(usuario)
    return None 


def deletar_usuario(session, id: int) -> UsuarioOut | None:
    """Busca um usuário pelo ID, remove do banco de dados e retorna os dados do usuário removido como UsuarioOut"""
    usuario = session.query(Usuario).filter(Usuario.id == id).first()
    if usuario:
        session.delete(usuario)
        session.commit()
        return UsuarioOut.model_validate(usuario)
    return None
