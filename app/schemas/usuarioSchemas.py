from pydantic import BaseModel, field_validator
from datetime import datetime
import re


class UsuarioBase(BaseModel):
    nome: str
    email: str
    senha: str
    carreira_id: int | None = None # usuário admin não precisa de carreira
    curso_id: int | None = None # usuário admin não precisa de curso

    @field_validator("email")
    def validar_email(valor: str) -> str:
        """Valida o formato do e-mail."""
        valor = valor.strip()
        if "@" not in valor:
            raise ValueError("E-mail inválido: deve conter '@'")
        try:
            dominio = valor.split("@", 1)[1]
        except Exception:
            raise ValueError("E-mail inválido")
        if "." not in dominio or dominio.startswith('.') or dominio.endswith('.'):
            raise ValueError("E-mail inválido")
        return valor

    @field_validator("senha")
    def validar_senha(valor: str) -> str:
        """Valida a senha. Regras: ao menos 6 caracteres, sem espaços, ao menos uma maiúscula e um caractere especial."""
        if len(valor) < 6:
            raise ValueError("Senha deve ter no mínimo 6 caracteres")
        if re.search(r"\s", valor):
            raise ValueError("Senha não pode conter espaços")
        if not re.search(r"[A-Z]", valor):
            raise ValueError("Senha deve conter ao menos uma letra maiúscula")
        if not re.search(r"[!@#$%^&*()_\-+=\[\]{};:'\",.<>\/?\\|]", valor):
            raise ValueError("Senha deve conter ao menos um caractere especial")
        return valor

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str
    admin: bool = False # por padrão, o usuário não é admin
    carreira_id: int | None = None
    curso_id: int | None = None
    criado_em: datetime
    atualizado_em: datetime

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}


class AtualizarUsuarioSchema(BaseModel):
    nome: str
    carreira_id: int
    curso_id: int
