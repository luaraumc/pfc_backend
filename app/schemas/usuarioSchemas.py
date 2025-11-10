from pydantic import BaseModel, field_validator # criação dos schemas e validação de campos
from datetime import datetime # campos de data e hora
from typing import List, Dict # tipos para listas e dicionários
import re # expressões regulares para validação de senha e e-mail

"""
Classes Base: representam os dados que serão enviados (POST). Não precisam dos campos autoincrement, pois são gerados pelo banco
Classes Out: herdam das Classes Base e representam os dados que serão retornados (GET). Precisam dos campos autoincrement
model_config = {'from_attributes': True}: permite que o Pydantic converta automaticamente objetos ORM do SQLAlchemy para schema
"""

# Schema de Usuario
class UsuarioBase(BaseModel):
    nome: str
    email: str
    senha: str
    admin: bool = False # por padrão, o usuário não é admin
    carreira_id: int | None = None # usuário admin não precisa de carreira
    curso_id: int | None = None # usuário admin não precisa de curso

    @field_validator("email")
    def validar_email(valor: str) -> str:
        valor = valor.strip()
        if "@" not in valor:
            raise ValueError("E-mail inválido: deve conter '@'")
        try:
            dominio = valor.split("@", 1)[1]
        except Exception:
            raise ValueError("E-mail inválido")
        # domínio deve conter ao menos um ponto (ex.: .com, .org, .edu.br) e não iniciar/terminar com ponto
        if "." not in dominio or dominio.startswith('.') or dominio.endswith('.'):
            raise ValueError("E-mail inválido")
        return valor

    @field_validator("senha")
    def validar_senha(valor: str) -> str:
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

class UsuarioOut(UsuarioBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

# Schema para atualização de usuário
class AtualizarUsuarioSchema(BaseModel):
    nome: str
    carreira_id: int
    curso_id: int