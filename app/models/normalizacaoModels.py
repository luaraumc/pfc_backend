from . import Base, Column, Integer, String, DateTime, func

class Normalizacao(Base):
    __tablename__ = 'normalizacao'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), unique=True, nullable=False)  # regex/padrão (ex.: r"^node(js)?$")
    nome_padronizado = Column(String(150), nullable=False)   # valor canônico (ex.: "Node.js")
    atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)