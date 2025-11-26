from pydantic import BaseModel
from datetime import datetime


class CategoriaBase(BaseModel):
    nome: str


class CategoriaOut(CategoriaBase):
    id: int
    atualizado_em: datetime

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}
