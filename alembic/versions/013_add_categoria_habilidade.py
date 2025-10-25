"""adiciona coluna categoria em habilidade

Revision ID: 013_add_categoria_habilidade
Revises: 012_unique_vaga_descricao
Create Date: 2025-10-16
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '013_add_categoria_habilidade'
down_revision = '012_unique_vaga_descricao'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('habilidade') as batch_op:
        batch_op.add_column(sa.Column('categoria', sa.String(length=120), nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('habilidade') as batch_op:
        batch_op.drop_column('categoria')
