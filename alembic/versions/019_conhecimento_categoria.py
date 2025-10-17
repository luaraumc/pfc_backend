"""muda relacao conhecimento_habilidade para conhecimento_categoria

Revision ID: 019_conhecimento_categoria
Revises: 018_seed_habilidades_from_const
Create Date: 2025-10-17
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '019_conhecimento_categoria'
down_revision = '018_seed_habilidades_from_const'
branch_labels = None
depends_on = None

def upgrade() -> None:
    conn = op.get_bind()

    # Cria nova tabela conhecimento_categoria
    op.create_table(
        'conhecimento_categoria',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('conhecimento_id', sa.Integer(), sa.ForeignKey('conhecimento.id', ondelete='CASCADE'), nullable=False),
        sa.Column('categoria_id', sa.Integer(), sa.ForeignKey('categoria.id', ondelete='CASCADE'), nullable=False),
    )
    op.create_unique_constraint('uq_conhecimento_categoria', 'conhecimento_categoria', ['conhecimento_id', 'categoria_id'])

    # Migrar dados: mapear conhecimento_habilidade -> conhecimento_categoria via categoria da habilidade
    # Apenas quando tabela antiga existir
    try:
        res = conn.execute(sa.text("SELECT 1 FROM conhecimento_habilidade LIMIT 1")).first()
        _ = res  # touch
        # Inserir pares distintos (conhecimento_id, categoria_id) derivados da tabela antiga
        conn.execute(sa.text(
            """
            INSERT INTO conhecimento_categoria (conhecimento_id, categoria_id)
            SELECT DISTINCT kh.conhecimento_id, h.categoria_id
            FROM conhecimento_habilidade kh
            JOIN habilidade h ON h.id = kh.habilidade_id
            WHERE h.categoria_id IS NOT NULL
            ON CONFLICT DO NOTHING
            """
        ))
    except Exception:
        # Se a tabela não existir, ignora
        pass

    # Opcional: manter tabela antiga por compatibilidade até atualização completa dos serviços
    # Caso deseje remover de imediato, descomente:
    # op.drop_table('conhecimento_habilidade')


def downgrade() -> None:
    # Não é trivial reconstruir conhecimento_habilidade a partir de conhecimento_categoria
    # Opção: apenas apagar a nova tabela
    op.drop_constraint('uq_conhecimento_categoria', 'conhecimento_categoria', type_='unique')
    op.drop_table('conhecimento_categoria')
