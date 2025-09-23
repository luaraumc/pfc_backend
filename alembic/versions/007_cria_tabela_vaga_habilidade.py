from alembic import op
import sqlalchemy as sa

# Revisões Alembic
revision = '007_cria_tabela_vaga_habilidade'
down_revision = '006_cria_tabela_vaga'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'vaga_habilidade',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('vaga_id', sa.Integer(), sa.ForeignKey('vaga.id', ondelete='CASCADE'), nullable=False),
        sa.Column('habilidade_id', sa.Integer(), sa.ForeignKey('habilidade.id', ondelete='CASCADE'), nullable=False),
    )
    op.create_unique_constraint('uq_vaga_habilidade', 'vaga_habilidade', ['vaga_id', 'habilidade_id'])


def downgrade():
    op.drop_constraint('uq_vaga_habilidade', 'vaga_habilidade', type_='unique')
    op.drop_table('vaga_habilidade')
