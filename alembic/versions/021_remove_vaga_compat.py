"""remove atualizado_em from vaga and drop compatibilidade table

Revision ID: 021_remove_vaga_compat
Revises: 020_add_peso
Create Date: 2025-10-29
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '021_remove_vaga_compat'
down_revision = '020_add_peso'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove coluna 'atualizado_em' da tabela 'vaga' caso exista
    try:
        with op.batch_alter_table('vaga') as batch_op:
            batch_op.drop_column('atualizado_em')
    except Exception:
        # ignora se a coluna não existir
        pass

    # Drop tabela 'compatibilidade' se existir
    conn = op.get_bind()
    try:
        conn.execute(sa.text('SELECT 1 FROM compatibilidade LIMIT 1'))
        op.drop_table('compatibilidade')
    except Exception:
        # se não existir, ignora
        pass


def downgrade() -> None:
    # Recria tabela 'compatibilidade' (estrutura mínima necessária)
    try:
        op.create_table(
            'compatibilidade',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('usuario_id', sa.Integer(), sa.ForeignKey('usuario.id', ondelete='SET NULL'), nullable=False),
            sa.Column('carreira_id', sa.Integer(), sa.ForeignKey('carreira.id', ondelete='SET NULL'), nullable=False),
            sa.Column('curso_id', sa.Integer(), sa.ForeignKey('curso.id', ondelete='SET NULL'), nullable=False),
            sa.Column('compatibilidade', sa.Numeric(5, 2), nullable=False),
            sa.Column('atualizado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )
    except Exception:
        # ignora se já existir
        pass

    # Re-adiciona coluna 'atualizado_em' na tabela 'vaga'
    try:
        with op.batch_alter_table('vaga') as batch_op:
            batch_op.add_column(sa.Column('atualizado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    except Exception:
        # ignora se já existir
        pass
