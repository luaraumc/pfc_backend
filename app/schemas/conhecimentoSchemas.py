from pydantic import BaseModel
from datetime import datetime 

class ConhecimentoBase(BaseModel):
    nome: str

class ConhecimentoOut(ConhecimentoBase):
    id: int
    atualizado_em: datetime

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}