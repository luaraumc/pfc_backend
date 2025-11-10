from . import Base, Column, Integer, ForeignKey, UniqueConstraint

# Modelo da tabela "conhecimento_categoria"
class ConhecimentoCategoria(Base):
    __tablename__ = 'conhecimento_categoria'
    id = Column(Integer, primary_key=True, index=True)
    conhecimento_id = Column(Integer, ForeignKey('conhecimento.id', ondelete='CASCADE'), nullable=False)
    categoria_id = Column(Integer, ForeignKey('categoria.id', ondelete='CASCADE'), nullable=False)
    peso = Column(Integer, nullable=True)
    __table_args__ = (
        UniqueConstraint('conhecimento_id', 'categoria_id', name='uq_conhecimento_categoria'),
    )