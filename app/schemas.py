from pydantic import BaseModel # criação dos schemas
from datetime import datetime # campos de data e hora

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

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

# Schema de Carreira
class CarreiraBase(BaseModel):
    nome: str
    descricao: str | None = None

class CarreiraOut(CarreiraBase):
    id: int
    atualizado_em: datetime

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

# Schema de Usuario
class UsuarioBase(BaseModel):
    nome: str
    email: str
    senha: str
    admin: bool = False # por padrão, o usuário não é admin
    carreira_id: int | None = None # usuário admin não precisa de carreira
    curso_id: int | None = None # usuário admin não precisa de curso

class UsuarioOut(UsuarioBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

# Schema de Habilidade
class HabilidadeBase(BaseModel):
    nome: str

class HabilidadeOut(HabilidadeBase):
    id: int
    atualizado_em: datetime

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

# Schema de Conhecimento
class ConhecimentoBase(BaseModel):
    nome: str

class ConhecimentoOut(ConhecimentoBase):
    id: int
    atualizado_em: datetime

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

# Schema de Compatibilidade
class CompatibilidadeBase(BaseModel):
    usuario_id: int
    carreira_id: int
    curso_id: int
    compatibilidade: float

class CompatibilidadeOut(CompatibilidadeBase):
    id: int
    atualizado_em: datetime

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

# Schema de RecuperacaoSenha
class RecuperacaoSenhaBase(BaseModel):
    usuario_id: int
    email: str
    codigo_recuperacao: str
    codigo_expira_em: datetime

class RecuperacaoSenhaOut(RecuperacaoSenhaBase):
    id: int

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

# Schema de LogExclusao
class LogExclusaoBase(BaseModel):
    email_hash: str
    acao: str = "exclusao definitiva"
    data_hora_exclusao: datetime | None = None
    responsavel: str = "usuario"
    motivo: str = "pedido do titular"

class LogExclusaoOut(LogExclusaoBase):
    id: int

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

# ===================== TABELAS RELACIONAIS =====================

# Schema de CursoConhecimento

class CursoConhecimentoBase(BaseModel):
    curso_id: int
    conhecimento_id: int

class CursoConhecimentoOut(CursoConhecimentoBase):
    id: int

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

#Schema de CarreiraHabilidade

class CarreiraHabilidadeBase(BaseModel):
    carreira_id: int
    habilidade_id: int

class CarreiraHabilidadeOut(CarreiraHabilidadeBase):
    id: int

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

# Schema de UsuarioHabilidade
class UsuarioHabilidadeBase(BaseModel):
    usuario_id: int
    habilidade_id: int

class UsuarioHabilidadeOut(UsuarioHabilidadeBase):
    id: int

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

#Schema de ConhecimentoHabilidade

class ConhecimentoHabilidadeBase(BaseModel):
    conhecimento_id: int
    habilidade_id: int

class ConhecimentoHabilidadeOut(ConhecimentoHabilidadeBase):
    id: int

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

# ===================== AUXILIARES =====================

class LoginSchema(BaseModel):
    email: str
    senha: str

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

class RecuperarSenhaSchema(BaseModel):
    email: str
    nova_senha: str

class AtualizarUsuarioSchema(BaseModel):
    nome: str
    email: str
    carreira_id: int
    curso_id: int

class AtualizarSenhaSchema(BaseModel):
    nova_senha: str

class ConfirmarNovaSenhaSchema(BaseModel):
    email: str
    codigo: str
    nova_senha: str
