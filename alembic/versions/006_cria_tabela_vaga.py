"""cria_tabela_vaga

Revision ID: 006_cria_tabela_vaga
Revises: 005_remove_email
Create Date: 2025-09-23
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_cria_tabela_vaga'
down_revision = '005_remove_email'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'vaga',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('titulo', sa.String(200), nullable=False, unique=True),
        sa.Column('descricao', sa.Text, nullable=False),
        sa.Column('criado_em', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('atualizado_em', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_vaga_titulo', 'vaga', ['titulo'])

def downgrade() -> None:
    try:
        op.drop_index('ix_vaga_titulo', table_name='vaga')
    except Exception:
        pass
    op.drop_table('vaga')
