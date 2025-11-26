from pydantic import BaseModel


class CursoConhecimentoBase(BaseModel):
    curso_id: int
    conhecimento_id: int


class CursoConhecimentoOut(CursoConhecimentoBase):
    id: int

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}
