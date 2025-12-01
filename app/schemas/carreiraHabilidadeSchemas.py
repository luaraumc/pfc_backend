from pydantic import BaseModel

class CarreiraHabilidadeBase(BaseModel):
    carreira_id: int
    habilidade_id: int
    frequencia: int

class CarreiraHabilidadeOut(CarreiraHabilidadeBase):
    id: int

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}