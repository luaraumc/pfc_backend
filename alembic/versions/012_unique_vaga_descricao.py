"""adiciona unique em vaga.descricao

Revision ID: 012_unique_vaga_descricao
Revises: 011_permite_null_vaga_carreira
Create Date: 2025-10-16
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012_unique_vaga_descricao'
down_revision = '011_permite_null_vaga_carreira'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar constraint única para descricao
    with op.batch_alter_table('vaga') as batch_op:
        batch_op.create_unique_constraint('uq_vaga_descricao', ['descricao'])


def downgrade() -> None:
    # Remover constraint única
    with op.batch_alter_table('vaga') as batch_op:
        batch_op.drop_constraint('uq_vaga_descricao', type_='unique')
