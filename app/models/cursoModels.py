from . import Base, Column, Integer,String, Text, DateTime, func


# Modelo da tabela "curso"
class Curso(Base):
	__tablename__ = 'curso'
	id = Column(Integer, primary_key=True, index=True)
	nome = Column(String(150), nullable=False)
	descricao = Column(Text, nullable=False)
	atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)