from . import Base, Column, Integer, ForeignKey, UniqueConstraint

# Modelo da tabela "carreira_habilidade"
class CarreiraHabilidade(Base):
    __tablename__ = 'carreira_habilidade'
    id = Column(Integer, primary_key=True, index=True)
    frequencia = Column(Integer, nullable=True)  # nova coluna para armazenar a frequência
    carreira_id = Column(Integer, ForeignKey('carreira.id', ondelete='CASCADE'), nullable=False)
    habilidade_id = Column(Integer, ForeignKey('habilidade.id', ondelete='CASCADE'), nullable=False)
    
    __table_args__ = (
        UniqueConstraint('carreira_id', 'habilidade_id', name='uq_carreira_habilidade'),
    )