from pydantic import BaseModel, field_validator # criação dos schemas e validação de campos
from datetime import datetime # campos de data e hora
from typing import List, Dict # tipos para listas e dicionários
import re # expressões regulares para validação de senha e e-mail

"""
Classes Base: representam os dados que serão enviados (POST). Não precisam dos campos autoincrement, pois são gerados pelo banco
Classes Out: herdam das Classes Base e representam os dados que serão retornados (GET). Precisam dos campos autoincrement
model_config = {'from_attributes': True}: permite que o Pydantic converta automaticamente objetos ORM do SQLAlchemy para schema
"""

# Schema de Login
class LoginSchema(BaseModel):
    email: str
    senha: str

    @field_validator("email")
    def validar_email_login(valor: str) -> str:
        valor = valor.strip()
        # Aceita qualquer domínio com um ponto (ex: .com, .org, .edu.br, .tech)
        if "@" not in valor:
            raise ValueError("E-mail inválido")
        try:
            dominio = valor.split("@", 1)[1]
        except Exception:
            raise ValueError("E-mail inválido")
        # domínio precisa ter ao menos um ponto e não começar/terminar com ponto
        if "." not in dominio or dominio.startswith('.') or dominio.endswith('.'):
            raise ValueError("E-mail inválido")
        return valor

    @field_validator("senha")
    def validar_senha_login(valor: str) -> str:
        if len(valor) < 6:
            raise ValueError("Senha inválida")
        if re.search(r"\s", valor):
            raise ValueError("Senha inválida")
        return valor

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

# Schemas para solicitação e confirmação de código de autenticação
class SolicitarCodigoSchema(BaseModel):
    email: str

class ConfirmarCodigoSchema(BaseModel):
    email: str
    codigo: str
    motivo: str

# Schema do código de autenticação
class CodigoAutenticacaoBase(BaseModel):
    usuario_id: int
    codigo_recuperacao: str
    codigo_expira_em: datetime
    motivo: str

# Schema para confirmação de nova senha
class ConfirmarNovaSenhaSchema(BaseModel):
    email: str
    codigo: str
    nova_senha: str

    @field_validator("nova_senha")
    def validar_nova_senha(valor: str) -> str:
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