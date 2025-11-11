from . import Base, Column, Integer, String, DateTime, ForeignKey, relationship, backref

class CodigoAutenticacao(Base):
	__tablename__ = "codigo_autenticacao"
	id = Column(Integer, primary_key=True, index=True)
	usuario_id = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), nullable=False)
	codigo_recuperacao = Column(String(255), nullable=False)
	codigo_expira_em = Column(DateTime, nullable=False)
	motivo = Column(String(50), nullable=False, server_default='recuperacao_senha')
	usuario = relationship(
		"Usuario",
		foreign_keys=[usuario_id], 
		passive_deletes=True, # garante que ao excluir o usuário, os códigos relacionados sejam excluídos automaticamente
		backref=backref("codigos_autenticacao", passive_deletes=True)
	)