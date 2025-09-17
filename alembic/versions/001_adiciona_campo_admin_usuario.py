"""adiciona_campo_admin_usuario

Revision ID: 001
Revises: 
Create Date: 2025-09-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Adiciona o campo admin na tabela usuario
    op.add_column('usuario', sa.Column('admin', sa.Boolean(), nullable=False, server_default=sa.false()))

    # Adiciona CHECK constraint: se admin = false, carreira_id e curso_id não podem ser NULL
    op.create_check_constraint(
        "chk_admin_carreira",
        "usuario",
        "(admin = true) OR (carreira_id IS NOT NULL AND curso_id IS NOT NULL)"
    )


def downgrade() -> None:
    # Remove a CHECK constraint
    op.drop_constraint("chk_admin_carreira", "usuario", type_="check")

    # Remove o campo admin
    op.drop_column('usuario', 'admin')

    
