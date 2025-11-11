from . import Base, Column, Integer, ForeignKey, UniqueConstraint

class UsuarioHabilidade(Base):
    __tablename__ = 'usuario_habilidade'
    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    habilidade_id = Column(Integer, ForeignKey('habilidade.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (
        UniqueConstraint('usuario_id', 'habilidade_id', name='uq_usuario_habilidade'),
    )

