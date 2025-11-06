from pydantic import ValidationError
from fastapi import HTTPException
import re


def format_validation_error(e: ValidationError) -> str:
    """Formata ValidationError do Pydantic para uma string legível.

    - remove prefixes como "Value error, " que às vezes aparecem
    - usa o último segmento de loc como campo e evita duplicação
    """
    errors = e.errors()
    messages: list[str] = []
    for err in errors:
        loc = ".".join(str(x) for x in err.get("loc", []))
        raw = err.get("msg", "")
        msg = re.sub(r'^[^,]+,\s*', '', raw)
        field = loc.split(".")[-1] if loc else ""
        if field and not msg.lower().startswith(field.lower()):
            messages.append(f"{field}: {msg}")
        else:
            messages.append(msg)
    return "; ".join(messages)


def raise_validation_http_exception(e: ValidationError) -> None:
    """Levanta HTTPException(422) com detail formatado.

    Usar dentro de except ValidationError as e: raise_validation_http_exception(e)
    """
    raise HTTPException(status_code=422, detail=format_validation_error(e))
