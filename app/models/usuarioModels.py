from . import Base, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func, relationship


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
	

