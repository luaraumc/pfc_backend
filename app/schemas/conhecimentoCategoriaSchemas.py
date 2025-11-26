from pydantic import BaseModel, field_validator


class ConhecimentoCategoriaBase(BaseModel):
    conhecimento_id: int
    categoria_id: int
    peso: int | None = None

    @field_validator("peso")
    def validar_peso(cls, v):
        """Valida o peso para estar entre 0 e 3, se fornecido."""
        if v is None:
            return v
        if not (0 <= v <= 3):
            raise ValueError("peso deve estar entre 0 e 3")
        return v


class ConhecimentoCategoriaOut(ConhecimentoCategoriaBase):
    id: int

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}


class ConhecimentoCategoriaAtualizar(BaseModel):
    categoria_id: int | None = None
    peso: int | None = None

    @field_validator("peso")
    def validar_peso(cls, v):
        """Valida o peso para estar entre 0 e 3, se fornecido."""
        if v is None:
            return v
        if not (0 <= v <= 3):
            raise ValueError("peso deve estar entre 0 e 3")
        return v
