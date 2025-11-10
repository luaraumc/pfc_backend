from pydantic import BaseModel, field_validator # criação dos schemas e validação de campos
from datetime import datetime # campos de data e hora
from typing import List, Dict # tipos para listas e dicionários
import re # expressões regulares para validação de senha e e-mail

"""
Classes Base: representam os dados que serão enviados (POST). Não precisam dos campos autoincrement, pois são gerados pelo banco
Classes Out: herdam das Classes Base e representam os dados que serão retornados (GET). Precisam dos campos autoincrement
model_config = {'from_attributes': True}: permite que o Pydantic converta automaticamente objetos ORM do SQLAlchemy para schema
"""

#Schema de ConhecimentoCategoria
class ConhecimentoCategoriaBase(BaseModel):
    conhecimento_id: int
    categoria_id: int
    peso: int | None = None

    @field_validator("peso")
    def validar_peso(cls, v):
        if v is None:
            return v
        if not (0 <= v <= 3):
            raise ValueError("peso deve estar entre 0 e 3")
        return v
    
class ConhecimentoCategoriaOut(ConhecimentoCategoriaBase):
    id: int

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

# Atualização parcial de ConhecimentoCategoria
class ConhecimentoCategoriaAtualizar(BaseModel):
    categoria_id: int | None = None
    peso: int | None = None

    @field_validator("peso")
    def validar_peso(cls, v):
        if v is None:
            return v
        if not (0 <= v <= 3):
            raise ValueError("peso deve estar entre 0 e 3")
        return v