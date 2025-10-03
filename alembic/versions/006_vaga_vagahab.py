"""cria tabela vaga e vaga_habilidade

Revision ID: 006_vaga_vagahab
Revises: 005_remove_email
Create Date: 2025-09-23
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_vaga_vagahab'
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
        sa.Column('carreira_id', sa.Integer, sa.ForeignKey('carreira.id', ondelete='SET NULL'), nullable=False),
    )
    op.create_index('ix_vaga_titulo', 'vaga', ['titulo'])
    op.create_index('ix_vaga_carreira_id', 'vaga', ['carreira_id'])

    op.create_table(
        'vaga_habilidade',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('vaga_id', sa.Integer, sa.ForeignKey('vaga.id', ondelete='CASCADE'), nullable=False),
        sa.Column('habilidade_id', sa.Integer, sa.ForeignKey('habilidade.id', ondelete='CASCADE'), nullable=False),
        sa.UniqueConstraint('vaga_id', 'habilidade_id', name='uq_vaga_habilidade'),
    )

def downgrade() -> None:
    op.drop_table('vaga_habilidade')
    op.drop_index('ix_vaga_carreira_id', table_name='vaga')
    op.drop_index('ix_vaga_titulo', table_name='vaga')
    op.drop_table('vaga')