"""permite null em vaga.carreira_id

Revision ID: 011_permite_null_vaga_carreira
Revises: 010_altera_nome_conhecimento
Create Date: 2025-10-13
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011_permite_null_vaga_carreira'
down_revision = '010_altera_nome_conhecimento'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Altera a coluna carreira_id para permitir NULL (mantendo o FK existente com ON DELETE SET NULL)
    with op.batch_alter_table('vaga') as batch_op:
        batch_op.alter_column(
            'carreira_id',
            existing_type=sa.Integer(),
            nullable=True,
            existing_nullable=False
        )


def downgrade() -> None:
    # Reverte para NOT NULL (pode falhar se houver linhas com NULL)
    with op.batch_alter_table('vaga') as batch_op:
        batch_op.alter_column(
            'carreira_id',
            existing_type=sa.Integer(),
            nullable=False,
            existing_nullable=True
        )
