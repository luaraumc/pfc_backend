"""add peso to conhecimento_categoria and drop conhecimento_habilidade

Revision ID: 020_add_peso
Revises: 019_conhecimento_categoria
Create Date: 2025-10-17
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '020_add_peso'
down_revision = '019_conhecimento_categoria'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adiciona coluna 'peso' em conhecimento_categoria
    op.add_column('conhecimento_categoria', sa.Column('peso', sa.Integer(), nullable=True))

    # Remove tabela conhecimento_habilidade se existir
    conn = op.get_bind()
    try:
        conn.execute(sa.text('SELECT 1 FROM conhecimento_habilidade LIMIT 1'))
        op.drop_table('conhecimento_habilidade')
    except Exception:
        # Se não existir, ignora
        pass


def downgrade() -> None:
    # Recria tabela conhecimento_habilidade de forma mínima (sem dados), pois dados foram migrados anteriormente
    conn = op.get_bind()
    try:
        op.create_table(
            'conhecimento_habilidade',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('conhecimento_id', sa.Integer(), sa.ForeignKey('conhecimento.id', ondelete='CASCADE'), nullable=False),
            sa.Column('habilidade_id', sa.Integer(), sa.ForeignKey('habilidade.id', ondelete='CASCADE'), nullable=False),
        )
        op.create_unique_constraint('uq_conhecimento_habilidade', 'conhecimento_habilidade', ['conhecimento_id', 'habilidade_id'])
    except Exception:
        pass
    # Remove coluna 'peso'
    with op.batch_alter_table('conhecimento_categoria') as batch_op:
        batch_op.drop_column('peso')
