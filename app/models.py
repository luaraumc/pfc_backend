from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric, UniqueConstraint, Boolean, CheckConstraint # tipos de dados e restrições
from sqlalchemy.sql import func # permite usar funções SQL, como NOW() para timestamps automáticos
from sqlalchemy.orm import relationship, backref # cria relacionamentos entre tabelas
from app.dependencies import Base # configuração da conexão com o banco de dados

# ===================== TABELAS PRINCIPAIS =====================

# Modelo da tabela "curso"
class Curso(Base):
	__tablename__ = 'curso'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), nullable=False)
	descricao = Column(Text, nullable=False)
	atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)

# Modelo tabela "carreira"
class Carreira(Base):
	__tablename__ = 'carreira'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), nullable=False)
	descricao = Column(Text)
	atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)

# Modelo da tabela "usuario"
class Usuario(Base):
	__tablename__ = 'usuario'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(100), nullable=False)
	email = Column(String(150), unique=True, nullable=False)
	senha = Column(Text, nullable=False)
	admin = Column(Boolean, default=False, nullable=False)
	carreira_id = Column(Integer, ForeignKey('carreira.id', ondelete='SET NULL'), nullable=True)
	curso_id = Column(Integer, ForeignKey('curso.id', ondelete='SET NULL'), nullable=True)
	criado_em = Column(DateTime, server_default=func.now(), nullable=False)
	atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)
	carreira = relationship('Carreira', backref='usuarios')
	curso = relationship('Curso', backref='usuarios')

# Modelo da tabela "habilidade"
class Habilidade(Base):
	__tablename__ = 'habilidade'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), unique=True, nullable=False)
	atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)

# Modelo da tabela "conhecimento"
class Conhecimento(Base):
	__tablename__ = 'conhecimento'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(300), unique=True, nullable=False)
	atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)

# Modelo da tabela "compatibilidade"
class Compatibilidade(Base):
	__tablename__ = 'compatibilidade'
	id = Column(Integer, primary_key=True, index=True)
	usuario_id = Column(Integer, ForeignKey('usuario.id', ondelete='SET NULL'), nullable=False)
	carreira_id = Column(Integer, ForeignKey('carreira.id', ondelete='SET NULL'), nullable=False)
	curso_id = Column(Integer, ForeignKey('curso.id', ondelete='SET NULL'), nullable=False)
	compatibilidade = Column(Numeric(5,2), nullable=False)
	atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)
	usuario = relationship('Usuario', backref='compatibilidades')
	carreira = relationship('Carreira', backref='compatibilidades')
	curso = relationship('Curso', backref='compatibilidades')

# Modelo da tabela "codigo_autenticacao" (códigos multiuso: recuperação de senha, atualização de senha, exclusão de conta)
class CodigoAutenticacao(Base):
	__tablename__ = "codigo_autenticacao"
	id = Column(Integer, primary_key=True, index=True)
	usuario_id = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
	codigo_recuperacao = Column(String(255), nullable=False)
	codigo_expira_em = Column(DateTime, nullable=False)
	motivo = Column(String(50), nullable=False, server_default='recuperacao_senha')
	usuario = relationship(
		"Usuario",
		foreign_keys=[usuario_id], # especifica qual coluna é a FK usada no relacionamento
		passive_deletes=True, # garante que ao excluir o usuário, os códigos relacionados sejam excluídos automaticamente
		backref=backref("codigos_autenticacao", passive_deletes=True)
	)

# Modelo da tabela "log_exclusoes"
class LogExclusao(Base):
	__tablename__ = 'log_exclusoes'
	id = Column(Integer, primary_key=True, index=True)
	email_hash = Column(String(128), nullable=False, index=True)
	acao = Column(String(50), nullable=False, server_default='exclusao definitiva')
	data_hora_exclusao = Column(DateTime, nullable=False, server_default=func.now())
	responsavel = Column(String(50), nullable=False, server_default='usuario')
	motivo = Column(String(100), nullable=False, server_default='pedido do titular')

# Modelo da tabela "vaga"
class Vaga(Base):
    __tablename__ = 'vaga'
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)  # removido unique=True
    descricao = Column(Text, nullable=False)
    criado_em = Column(DateTime, server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)
    carreira_id = Column(Integer, ForeignKey("carreira.id", ondelete="SET NULL"), nullable=True)
    carreira = relationship("Carreira", backref="vagas")

# backref: cria um relacionamento bidirecional entre os modelos

# ===================== TABELAS RELACIONAIS =====================

# Modelo da tabela "curso_conhecimento"
class CursoConhecimento(Base):
    __tablename__ = 'curso_conhecimento'
    id = Column(Integer, primary_key=True, index=True)
    curso_id = Column(Integer, ForeignKey('curso.id', ondelete='CASCADE'), nullable=False)
    conhecimento_id = Column(Integer, ForeignKey('conhecimento.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (
        UniqueConstraint('curso_id', 'conhecimento_id', name='uq_curso_conhecimento'),
    )

# Modelo da tabela "carreira_habilidade"
class CarreiraHabilidade(Base):
    __tablename__ = 'carreira_habilidade'
    id = Column(Integer, primary_key=True, index=True)
    frequencia = Column(Integer, nullable=True) # nova coluna para armazenar a frequência
    carreira_id = Column(Integer, ForeignKey('carreira.id', ondelete='CASCADE'), nullable=False)
    habilidade_id = Column(Integer, ForeignKey('habilidade.id', ondelete='CASCADE'), nullable=False)
	
    __table_args__ = (
        UniqueConstraint('carreira_id', 'habilidade_id', name='uq_carreira_habilidade'),
    )


# Modelo da tabela "usuario_habilidade"
class UsuarioHabilidade(Base):
    __tablename__ = 'usuario_habilidade'
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    habilidade_id = Column(Integer, ForeignKey('habilidade.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (
        UniqueConstraint('usuario_id', 'habilidade_id', name='uq_usuario_habilidade'),
    )

# Modelo da tabela "conhecimento_habilidade"
class ConhecimentoHabilidade(Base):
    __tablename__ = 'conhecimento_habilidade'
    id = Column(Integer, primary_key=True, index=True)
    conhecimento_id = Column(Integer, ForeignKey('conhecimento.id', ondelete='CASCADE'), nullable=False)
    habilidade_id = Column(Integer, ForeignKey('habilidade.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (
        UniqueConstraint('conhecimento_id', 'habilidade_id', name='uq_conhecimento_habilidade'),
    )

# Modelo da tabela "vaga_habilidade"
class VagaHabilidade(Base):
    __tablename__ = 'vaga_habilidade'
    id = Column(Integer, primary_key=True, index=True)
    vaga_id = Column(Integer, ForeignKey('vaga.id', ondelete='CASCADE'), nullable=False)
    habilidade_id = Column(Integer, ForeignKey('habilidade.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (
        UniqueConstraint('vaga_id', 'habilidade_id', name='uq_vaga_habilidade'),
    )

# ondelete='CASCADE': garante que ao excluir o registro principal os relacionados também sejam excluídos
# UniqueConstraint: garante que não haja duplicidade