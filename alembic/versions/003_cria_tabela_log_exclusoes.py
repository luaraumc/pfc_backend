"""cria_tabela_log_exclusoes

Revision ID: 003_log_exclusoes
Revises: 002_allow_null_carreira_curso
Create Date: 2025-09-18
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '003_log_exclusoes'
down_revision = '002_allow_null_carreira_curso'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'log_exclusoes',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('email_hash', sa.String(128), nullable=False, index=True),
        sa.Column('acao', sa.String(50), nullable=False, server_default='exclusao definitiva'),
        sa.Column('data_hora_exclusao', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('responsavel', sa.String(50), nullable=False, server_default='usuario'),
        sa.Column('motivo', sa.String(100), nullable=False, server_default='pedido do titular')
    )

def downgrade() -> None:
    op.drop_table('log_exclusoes')
