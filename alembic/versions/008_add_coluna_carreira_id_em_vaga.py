"""Add carreira_id em vaga"""

from alembic import op
import sqlalchemy as sa

# Revisões
revision = "008_add_coluna_carreira_id_em_vaga"
down_revision = "007_cria_tabela_vaga_habilidade"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "vaga",
        sa.Column("carreira_id", sa.Integer(), sa.ForeignKey("carreira.id", ondelete="SET NULL"), nullable=True)
    )
    op.create_index("ix_vaga_carreira_id", "vaga", ["carreira_id"])

def downgrade():
    op.drop_index("ix_vaga_carreira_id", table_name="vaga")
    op.drop_column("vaga", "carreira_id")