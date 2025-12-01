from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, List, Tuple


def make_obj(**attrs: Any) -> Any:
    """Cria um objeto simples com atributos arbitrários.
    Útil para testar Pydantic .model_validate(from_attributes=True).
    """
    return SimpleNamespace(**attrs)


def rel(id: Any, nome: Any, score: Any) -> Dict[str, Any]:
    """Atalho para criar dicionários de relação com score (usado em MapaOut)."""
    return {"id": id, "nome": nome, "score": score}


def senha_valida() -> str:
    """Retorna uma senha válida segundo as regras dos testes: >=6, 1 maiúscula, 1 especial, sem espaços."""
    return "Abc!12"


def invalid_emails() -> List[str]:
    """Conjunto de e-mails inválidos usados pelos testes de schemas."""
    vals = {
        # usados em auth
        "userexample.com",      # sem @
        "user@domain",          # sem ponto no domínio
        "user@.com",            # domínio inicia com ponto
        "user@domain.",         # domínio termina com ponto
        "user@",                # sem domínio
        # usados em usuario
        "userdomain.com",       # sem @
        "user@dominio",         # sem ponto no domínio
        "user@com.",            # domínio termina com ponto
    }
    return list(vals)


def invalid_passwords_usuario() -> List[str]:
    """Senhas inválidas comuns usadas nos testes de UsuarioBase."""
    return [
        "Ab!1",     # < 6
        "Abc 12!",  # espaço
        "abc123!",  # sem maiúscula
        "Abc123",   # sem especial
    ]
