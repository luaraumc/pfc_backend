"""altera tamanho do campo nome em conhecimento para 300

Revision ID: 010_altera_nome_conhecimento
Revises: 009_add_frequencia
Create Date: 2025-10-06
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010_altera_nome_conhecimento'
down_revision = '009_add_frequencia'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.alter_column('conhecimento', 'nome',
        type_=sa.String(300),
        existing_type=sa.String(150),
        existing_nullable=False
    )

def downgrade() -> None:
    op.alter_column('conhecimento', 'nome',
        type_=sa.String(150),
        existing_type=sa.String(300),
        existing_nullable=False
    )
