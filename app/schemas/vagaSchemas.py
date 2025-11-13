from pydantic import BaseModel

class VagaBase(BaseModel):
    titulo: str
    descricao: str
    carreira_id: int | None = None

class VagaOut(VagaBase):
    id: int
    carreira_nome: str | None = None
    
    model_config = {'from_attributes': True}