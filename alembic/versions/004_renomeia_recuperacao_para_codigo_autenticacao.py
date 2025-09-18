"""renomeia_recuperacao_para_codigo_autenticacao

Revision ID: 004_codigo_autenticacao
Revises: 003_log_exclusoes
Create Date: 2025-09-18
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_codigo_autenticacao'
down_revision = '003_log_exclusoes'
branch_labels = None
depends_on = None

old_table = 'recuperacao_senha'
new_table = 'codigo_autenticacao'


def upgrade() -> None:
    # Renomeia a tabela
    op.rename_table(old_table, new_table)

    # Adiciona coluna motivo
    op.add_column(new_table, sa.Column('motivo', sa.String(50), nullable=False, server_default='recuperacao_senha'))

    # Opcional: índice por email + motivo para busca rápida
    op.create_index('ix_codigo_autenticacao_email_motivo', new_table, ['email','motivo'])


def downgrade() -> None:
    # Remove índice
    try:
        op.drop_index('ix_codigo_autenticacao_email_motivo', table_name=new_table)
    except Exception:
        pass

    # Remove coluna
    with op.batch_alter_table(new_table) as batch_op:
        try:
            batch_op.drop_column('motivo')
        except Exception:
            pass

    # Renomeia de volta
    op.rename_table(new_table, old_table)
