from . import Base, Column, Integer, ForeignKey, UniqueConstraint

class CursoConhecimento(Base):
    __tablename__ = 'curso_conhecimento'
    id = Column(Integer, primary_key=True, index=True)
    curso_id = Column(Integer, ForeignKey('curso.id', ondelete='CASCADE'), nullable=False)
    conhecimento_id = Column(Integer, ForeignKey('conhecimento.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (
        UniqueConstraint('curso_id', 'conhecimento_id', name='uq_curso_conhecimento'),
    )