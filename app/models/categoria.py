from . import Base, Column, Integer, String, DateTime, func

# Modelo da tabela "categoria"
class Categoria(Base):
    __tablename__ = 'categoria'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), unique=True, nullable=False)
    atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)