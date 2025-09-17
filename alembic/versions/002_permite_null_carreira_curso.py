from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "002_allow_null_carreira_curso"
down_revision = "001"
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column("usuario", "carreira_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("usuario", "curso_id", existing_type=sa.Integer(), nullable=True)
    # Recria o check (caso já exista, primeiro remova)
    try:
        op.drop_constraint("chk_admin_carreira", "usuario", type_="check")
    except Exception:
        pass
    op.create_check_constraint(
        "chk_admin_carreira",
        "usuario",
        "(admin = true) OR (carreira_id IS NOT NULL AND curso_id IS NOT NULL)",
    )

def downgrade():
    op.drop_constraint("chk_admin_carreira", "usuario", type_="check")
    op.alter_column("usuario", "carreira_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("usuario", "curso_id", existing_type=sa.Integer(), nullable=False)