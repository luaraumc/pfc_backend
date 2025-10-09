"""adiciona coluna frequencia em carreira_habilidade

Revision ID: 009_add_frequencia
Revises: 008_remove_chk_admin_carreira
Create Date: 2025-10-06
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009_add_frequencia'
down_revision = '008_remove_chk_admin_carreira'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adiciona coluna frequencia
    op.add_column('carreira_habilidade', sa.Column('frequencia', sa.Integer(), nullable=True, default=0))


def downgrade() -> None:
    # Remove coluna frequencia
    op.drop_column('carreira_habilidade', 'frequencia')