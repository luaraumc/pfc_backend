from pydantic import BaseModel
from datetime import datetime


class LogExclusaoBase(BaseModel):
    email_hash: str
    acao: str = "exclusao definitiva"
    data_hora_exclusao: datetime | None = None
    responsavel: str = "usuario"
    motivo: str = "pedido do titular"


class LogExclusaoOut(LogExclusaoBase):
    id: int

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}
