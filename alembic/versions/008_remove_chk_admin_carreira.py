from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "008_remove_chk_admin_carreira"
down_revision = "007_remove_unique_vaga_titulo"
branch_labels = None
depends_on = None

def upgrade():
    # Remove a check constraint que exige carreira_id e curso_id quando não-admin
    try:
        op.drop_constraint("chk_admin_carreira", "usuario", type_="check")
    except Exception:
        # Caso já não exista, ignorar
        pass


def downgrade():
    # Restaura a constraint original
    op.create_check_constraint(
        "chk_admin_carreira",
        "usuario",
        "(admin = true) OR (carreira_id IS NOT NULL AND curso_id IS NOT NULL)",
    )
