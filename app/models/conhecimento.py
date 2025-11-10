from . import Base, Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, func

# Modelo da tabela "conhecimento"
class Conhecimento(Base):
    __tablename__ = 'conhecimento'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(300), unique=True, nullable=False)
    atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)

