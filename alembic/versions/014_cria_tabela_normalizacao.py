"""cria tabela normalizacao

Revision ID: 014_cria_tabela_normalizacao
Revises: 013_add_categoria_habilidade
Create Date: 2025-10-16
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '014_cria_tabela_normalizacao'
down_revision = '013_add_categoria_habilidade'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'normalizacao',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=200), nullable=False),
        sa.Column('nome_padronizado', sa.String(length=150), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_normalizacao_id'), 'normalizacao', ['id'], unique=False)
    op.create_unique_constraint('uq_normalizacao_nome', 'normalizacao', ['nome'])


def downgrade() -> None:
    op.drop_constraint('uq_normalizacao_nome', 'normalizacao', type_='unique')
    op.drop_index(op.f('ix_normalizacao_id'), table_name='normalizacao')
    op.drop_table('normalizacao')
