"""cria tabela categoria e migra coluna categoria de habilidade para categoria_id

Revision ID: 016_cria_tabela_categoria_e_migracao
Revises: 015_seed_normalizacao_from_const
Create Date: 2025-10-17
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '016_cria_tabela_categoria'
down_revision = '015_seed_normalizacao_from_const'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Criar tabela categoria (apenas estrutura)
    op.create_table(
        'categoria',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('nome', sa.String(length=150), nullable=False, unique=True),
        sa.Column('atualizado_em', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    )

    # 2) Alterar tabela habilidade: adicionar categoria_id (inicialmente nullable) e criar FK; remover coluna antiga 'categoria'
    with op.batch_alter_table('habilidade') as batch_op:
        batch_op.add_column(sa.Column('categoria_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_habilidade_categoria', 'categoria', ['categoria_id'], ['id'], ondelete='RESTRICT'
        )
        batch_op.drop_column('categoria')


def downgrade() -> None:
    # 1) Recriar coluna antiga de categoria como string (apenas estrutural)
    with op.batch_alter_table('habilidade') as batch_op:
        batch_op.add_column(sa.Column('categoria', sa.String(length=120), nullable=True))

    # 2) Remover FK e coluna categoria_id
    with op.batch_alter_table('habilidade') as batch_op:
        batch_op.drop_constraint('fk_habilidade_categoria', type_='foreignkey')
        batch_op.drop_column('categoria_id')

    # 3) Remover tabela categoria
    op.drop_table('categoria')
