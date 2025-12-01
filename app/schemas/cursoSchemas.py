from pydantic import BaseModel
from datetime import datetime # campos de data e hora

class CursoBase(BaseModel):
    nome: str
    descricao: str

class CursoOut(CursoBase):
    id: int
    atualizado_em: datetime

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}