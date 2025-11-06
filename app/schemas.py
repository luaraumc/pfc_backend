from pydantic import BaseModel, field_validator # criação dos schemas e validação de campos
from datetime import datetime # campos de data e hora
from typing import List, Dict # tipos para listas e dicionários
import re # expressões regulares para validação de senha e e-mail

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

    @field_validator("email")
    def validar_email(valor: str) -> str:
        valor = valor.strip()
        if "@" not in valor:
            raise ValueError("E-mail inválido: deve conter '@'")
        try:
            dominio = valor.split("@", 1)[1].lower() # obtém o domínio após o '@'
        except Exception:
            raise ValueError("E-mail inválido")
        if ".com" not in dominio:
            raise ValueError("E-mail inválido: domínio deve conter '.com'")
        return valor

    @field_validator("senha")
    def validar_senha(valor: str) -> str:
        if len(valor) < 6:
            raise ValueError("Senha deve ter no mínimo 6 caracteres")
        if re.search(r"\s", valor):
            raise ValueError("Senha não pode conter espaços")
        if not re.search(r"[A-Z]", valor):
            raise ValueError("Senha deve conter ao menos uma letra maiúscula")
        if not re.search(r"[!@#$%^&*()_\-+=\[\]{};:'\",.<>\/?\\|]", valor):
            raise ValueError("Senha deve conter ao menos um caractere especial")
        return valor

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

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
    categoria_id: int
    atualizado_em: datetime
    categoria: str | None = None

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

# Schemas de Categoria
class CategoriaBase(BaseModel):
    nome: str

class CategoriaOut(CategoriaBase):
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

# Schema de RecuperacaoSenha
class CodigoAutenticacaoBase(BaseModel):
    usuario_id: int
    codigo_recuperacao: str
    codigo_expira_em: datetime
    motivo: str

class CodigoAutenticacaoOut(CodigoAutenticacaoBase):
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

# Schema de Vaga
class VagaBase(BaseModel):
    titulo: str
    descricao: str
    carreira_id: int | None = None

class VagaOut(VagaBase):
    id: int
    carreira_nome: str | None = None
    
    model_config = {'from_attributes': True}


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
    frequencia: int  # nova coluna para frequência

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

#Schema de VagaHabilidade

class VagaHabilidadeBase(BaseModel):
    vaga_id: int
    habilidade_id: int

class VagaHabilidadeOut(VagaHabilidadeBase):
    id: int

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}


# ===================== AUXILIARES =====================

class LoginSchema(BaseModel):
    email: str
    senha: str

    @field_validator("email")
    def validar_email_login(valor: str) -> str:
        valor = valor.strip()
        if "@" not in valor:
            raise ValueError("E-mail inválido")
        try:
            dominio = valor.split("@", 1)[1].lower()
        except Exception:
            raise ValueError("E-mail inválido")
        if ".com" not in dominio:
            raise ValueError("E-mail inválido")
        return valor

    @field_validator("senha")
    def validar_senha_login(valor: str) -> str:
        if len(valor) < 6:
            raise ValueError("Senha inválida")
        if re.search(r"\s", valor):
            raise ValueError("Senha inválida")
        return valor

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

class AtualizarUsuarioSchema(BaseModel):
    nome: str
    carreira_id: int
    curso_id: int

class HabilidadeAtualizar(BaseModel):
    nome: str | None = None
    categoria_id: int | None = None

class SolicitarCodigoSchema(BaseModel):
    email: str

class ConfirmarCodigoSchema(BaseModel):
    email: str
    codigo: str
    motivo: str

class ConfirmarNovaSenhaSchema(BaseModel):
    email: str
    codigo: str
    nova_senha: str

    @field_validator("nova_senha")
    def validar_nova_senha(valor: str) -> str:
        if len(valor) < 6:
            raise ValueError("Nova senha deve ter no mínimo 6 caracteres")
        if re.search(r"\s", valor):
            raise ValueError("Nova senha não pode conter espaços")
        if not re.search(r"[A-Z]", valor):
            raise ValueError("Nova senha deve conter ao menos uma letra maiúscula")
        if not re.search(r"[!@#$%^&*()_\-+=\[\]{};:'\",.<>\/?\\|]", valor):
            raise ValueError("Nova senha deve conter ao menos um caractere especial")
        return valor

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}

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
