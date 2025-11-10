from pydantic import BaseModel, field_validator # criação dos schemas e validação de campos
from datetime import datetime # campos de data e hora
from typing import List, Dict # tipos para listas e dicionários
import re # expressões regulares para validação de senha e e-mail

"""
Classes Base: representam os dados que serão enviados (POST). Não precisam dos campos autoincrement, pois são gerados pelo banco
Classes Out: herdam das Classes Base e representam os dados que serão retornados (GET). Precisam dos campos autoincrement
model_config = {'from_attributes': True}: permite que o Pydantic converta automaticamente objetos ORM do SQLAlchemy para schema
"""

class ItemSimples(BaseModel):
    id: int
    nome: str

class RelacaoScore(BaseModel):
    id: int
    nome: str
    score: float

class MapaOut(BaseModel):
    cursos: List[ItemSimples]
    carreiras: List[ItemSimples]
    cursoToCarreiras: Dict[int, List[RelacaoScore]]
    carreiraToCursos: Dict[int, List[RelacaoScore]]
