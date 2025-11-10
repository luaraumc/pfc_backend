from . import Base, Column, Integer, String, DateTime, ForeignKey, func, relationship

# Modelo da tabela "habilidade"
class Habilidade(Base):
    __tablename__ = 'habilidade'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), unique=True, nullable=False)
    categoria_id = Column(Integer, ForeignKey('categoria.id', ondelete='RESTRICT'), nullable=False)
    atualizado_em = Column(DateTime, server_default=func.now(), nullable=False)
    categoria_rel = relationship('Categoria', backref='habilidades')

    # leitura do nome da categoria para mostrar no front
    @property
    def categoria(self) -> str | None:
        return getattr(self.categoria_rel, 'nome', None)