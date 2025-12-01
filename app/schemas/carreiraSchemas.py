from pydantic import BaseModel
from datetime import datetime


class CarreiraBase(BaseModel):
    nome: str
    descricao: str | None = None

class CarreiraOut(CarreiraBase):
    id: int
    atualizado_em: datetime

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}