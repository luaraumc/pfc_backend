from pydantic import BaseModel

class UsuarioHabilidadeBase(BaseModel):
    usuario_id: int
    habilidade_id: int

class UsuarioHabilidadeOut(UsuarioHabilidadeBase):
    id: int

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}