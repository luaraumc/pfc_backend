from . import Base, Column, Integer, ForeignKey, UniqueConstraint

class VagaHabilidade(Base):
    __tablename__ = 'vaga_habilidade'
    id = Column(Integer, primary_key=True, index=True)
    vaga_id = Column(Integer, ForeignKey('vaga.id', ondelete='CASCADE'), nullable=False)
    habilidade_id = Column(Integer, ForeignKey('habilidade.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (
        UniqueConstraint('vaga_id', 'habilidade_id', name='uq_vaga_habilidade'),
    )