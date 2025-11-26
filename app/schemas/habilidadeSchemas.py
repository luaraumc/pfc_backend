from pydantic import BaseModel
from datetime import datetime


class HabilidadeBase(BaseModel):
    nome: str


class HabilidadeOut(HabilidadeBase):
    id: int
    categoria_id: int
    atualizado_em: datetime
    categoria: str | None = None

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}


class HabilidadeAtualizar(BaseModel):
    nome: str | None = None
    categoria_id: int | None = None
