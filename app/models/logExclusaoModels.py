from . import Base, Column, Integer, String, DateTime, func

class LogExclusao(Base):
	__tablename__ = 'log_exclusoes'
	id = Column(Integer, primary_key=True, index=True)
	email_hash = Column(String(128), nullable=False, index=True)
	acao = Column(String(50), nullable=False, server_default='exclusao definitiva')
	data_hora_exclusao = Column(DateTime, nullable=False, server_default=func.now())
	responsavel = Column(String(50), nullable=False, server_default='usuario')
	motivo = Column(String(100), nullable=False, server_default='pedido do titular')