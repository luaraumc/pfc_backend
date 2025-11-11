from . import Base, Column, Integer, String, Text, DateTime, ForeignKey, func, relationship

class Vaga(Base):
    __tablename__ = 'vaga'
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)  # removido unique=True
    descricao = Column(Text, nullable=False, unique=True)
    criado_em = Column(DateTime, server_default=func.now(), nullable=False)
    carreira_id = Column(Integer, ForeignKey("carreira.id", ondelete="SET NULL"), nullable=True)
    carreira = relationship("Carreira", backref="vagas")
