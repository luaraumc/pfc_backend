from . import Base, Column, Integer, String, Text, DateTime, func

class Carreira(Base):
	__tablename__ = 'carreira'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), nullable=False)
	descricao = Column(Text)
	atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)