from pydantic import ValidationError
from fastapi import HTTPException
import re


def format_validation_error(e: ValidationError) -> str:
    """Formata ValidationError do Pydantic para uma string legível.

    - remove prefixos antes da primeira vírgula (ex.: "Value error, ")
    - usa o último segmento de loc (localização do erro/o caminho até o valor inválido nos dados ) como "campo" e evita duplicação
    """

    errors = e.errors()
    messages: list[str] = []

    for err in errors:
        loc = ".".join(str(x) for x in err.get("loc", []))  # junta loc em uma string "a.b.c"
        raw = err.get("msg", "")  # mensagem original
        msg = re.sub(r'^[^,]+,\s*', '', raw)  # remove qualquer prefixo até a primeira vírgula
        field = loc.split(".")[-1] if loc else ""  # último segmento de loc

        # evita duplicação do nome do campo na mensagem
        if field and not msg.lower().startswith(field.lower()):
            messages.append(f"{field}: {msg}")
        else:
            messages.append(msg)
    return "; ".join(messages)


def raise_validation_http_exception(e: ValidationError) -> None:
    """Levanta HTTPException(422) com detail formatado.
    """
    raise HTTPException(status_code=422, detail=format_validation_error(e))
