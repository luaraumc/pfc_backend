from pydantic import BaseModel, field_validator
from datetime import datetime
import re

class LoginSchema(BaseModel):
    email: str
    senha: str

    @field_validator("email")
    def validar_email_login(valor: str) -> str:
        """Valida o formato do e-mail."""
        valor = valor.strip()
        if "@" not in valor:
            raise ValueError("E-mail inválido")
        try:
            dominio = valor.split("@", 1)[1]
        except Exception:
            raise ValueError("E-mail inválido")
        if "." not in dominio or dominio.startswith('.') or dominio.endswith('.'):
            raise ValueError("E-mail inválido")
        return valor

    @field_validator("senha")
    def validar_senha_login(valor: str) -> str:
        """Valida a senha do login. Regras: ao menos 6 caracteres, sem espaços."""
        if len(valor) < 6:
            raise ValueError("Senha inválida")
        if re.search(r"\s", valor):
            raise ValueError("Senha inválida")
        return valor

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}


class SolicitarCodigoSchema(BaseModel):
    email: str

class ConfirmarCodigoSchema(BaseModel):
    email: str
    codigo: str
    motivo: str


class CodigoAutenticacaoBase(BaseModel):
    usuario_id: int
    codigo_recuperacao: str
    codigo_expira_em: datetime
    motivo: str


class ConfirmarNovaSenhaSchema(BaseModel):
    email: str
    codigo: str
    nova_senha: str

    @field_validator("nova_senha")
    def validar_nova_senha(valor: str) -> str:
        """Valida a nova senha. Regras: ao menos 6 caracteres, sem espaços, ao menos uma maiúscula e um caractere especial."""
        if len(valor) < 6:
            raise ValueError("Nova senha deve ter no mínimo 6 caracteres")
        if re.search(r"\s", valor):
            raise ValueError("Nova senha não pode conter espaços")
        if not re.search(r"[A-Z]", valor):
            raise ValueError("Nova senha deve conter ao menos uma letra maiúscula")
        if not re.search(r"[!@#$%^&*()_\-+=\[\]{};:'\",.<>\/?\\|]", valor):
            raise ValueError("Nova senha deve conter ao menos um caractere especial")
        return valor

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}