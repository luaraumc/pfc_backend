"""remove unicidade do titulo da vaga

Revision ID: 007_remove_unique_vaga_titulo
Revises: 006_vaga_vagahab
Create Date: 2025-10-03
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_remove_unique_vaga_titulo'
down_revision = '006_vaga_vagahab'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Remove constraint UNIQUE do título
    with op.batch_alter_table('vaga') as batch_op:
        batch_op.drop_constraint('vaga_titulo_key', type_='unique')

def downgrade() -> None:
    # Recria constraint UNIQUE do título
    with op.batch_alter_table('vaga') as batch_op:
        batch_op.create_unique_constraint('vaga_titulo_key', ['titulo'])
