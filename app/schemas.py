import datetime
from pydantic import BaseModel


"""
Classes Base: representam os dados que serão enviados (POST). Não precisam dos campos autoincrement, pois são gerados pelo banco
Classes Out: herdam das Classes Base e representam os dados que serão retornados (GET). Precisam dos campos autoincrement
model_config = {'from_attributes': True}: permite que o Pydantic converta automaticamente objetos ORM do SQLAlchemy para schema
"""

# ===================== TABELAS PRINCIPAIS =====================

# Schema de Curso
class CursoBase(BaseModel):
    nome: str
    descricao: str

class CursoOut(CursoBase):
    id: int
    atualizado_em: datetime
    model_config = {'from_attributes': True}

# Schema de Carreira
class CarreiraBase(BaseModel):
    nome: str
    descricao: str

class CarreiraOut(CarreiraBase):
    id: int
    atualizado_em: datetime

    model_config = {'from_attributes': True}

# Schema de Usuario
class UsuarioBase(BaseModel):
    nome: str
    email: str
    senha: str
    carreira_id: int
    curso_id: int

class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str
    carreira_id: int
    curso_id: int
    criado_em: datetime
    atualizado_em: datetime

    model_config = {'from_attributes': True}

# Schema de Habilidade
class HabilidadeBase(BaseModel):
    nome: str

class HabilidadeOut(HabilidadeBase):
    id: int
    atualizado_em: datetime

    model_config = {'from_attributes': True}

# Schema de Conhecimento
class ConhecimentoBase(BaseModel):
    nome: str

class ConhecimentoOut(ConhecimentoBase):
    id: int
    atualizado_em: datetime

    model_config = {'from_attributes': True}

# Schema de Compatibilidade
class CompatibilidadeBase(BaseModel):
    usuario_id: int
    carreira_id: int
    curso_id: int
    compatibilidade: float

class CompatibilidadeOut(CompatibilidadeBase):
    id: int
    atualizado_em: datetime

    model_config = {'from_attributes': True}

# ===================== TABELAS RELACIONAIS =====================

# Schema de CursoConhecimento
class CursoConhecimentoBase(BaseModel):
    curso_id: int
    conhecimento_id: int

class CursoConhecimentoOut(CursoConhecimentoBase):
    id: int

    model_config = {'from_attributes': True}

# Schema de CarreiraHabilidade
class CarreiraHabilidadeBase(BaseModel):
    carreira_id: int
    habilidade_id: int

class CarreiraHabilidadeOut(CarreiraHabilidadeBase):
    id: int

    model_config = {'from_attributes': True}

# Schema de UsuarioHabilidade
class UsuarioHabilidadeBase(BaseModel):
    usuario_id: int
    habilidade_id: int

class UsuarioHabilidadeOut(UsuarioHabilidadeBase):
    id: int

    model_config = {'from_attributes': True}

# Schema de ConhecimentoHabilidade
class ConhecimentoHabilidadeBase(BaseModel):
    conhecimento_id: int
    habilidade_id: int

class ConhecimentoHabilidadeOut(ConhecimentoHabilidadeBase):
    id: int

    model_config = {'from_attributes': True}