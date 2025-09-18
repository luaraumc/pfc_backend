"""remove_email_from_codigo_autenticacao

Revision ID: 005_remove_email
Revises: 004_codigo_autenticacao
Create Date: 2025-09-18
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_remove_email'
down_revision = '004_codigo_autenticacao'
branch_labels = None
depends_on = None

table_name = 'codigo_autenticacao'


def upgrade() -> None:
    # Drop old index by email+motivo if exists
    try:
        op.drop_index('ix_codigo_autenticacao_email_motivo', table_name=table_name)
    except Exception:
        pass

    # Drop email column safely (dropping the column will implicitly drop its FK, if any)
    with op.batch_alter_table(table_name) as batch_op:
        try:
            batch_op.drop_column('email')
        except Exception:
            pass

    # Ensure FK on usuario_id has ON DELETE CASCADE
    # Drop any existing FK(s) on usuario_id dynamically to avoid name mismatch
    conn = op.get_bind()
    res = conn.execute(sa.text(
        """
        SELECT tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.constraint_schema = kcu.constraint_schema
        WHERE tc.table_name = :table
          AND tc.constraint_type = 'FOREIGN KEY'
          AND kcu.column_name = 'usuario_id'
        """
    ), {"table": table_name}).fetchall()
    for row in res:
        op.execute(sa.text(f'ALTER TABLE {table_name} DROP CONSTRAINT "{row[0]}"'))

    with op.batch_alter_table(table_name) as batch_op:
        batch_op.create_foreign_key(
            'codigo_autenticacao_usuario_id_fkey',
            referent_table='usuario',
            local_cols=['usuario_id'],
            remote_cols=['id'],
            ondelete='CASCADE'
        )

    # Create helpful index by (usuario_id, motivo)
    op.create_index('ix_codigo_autenticacao_usuario_motivo', table_name, ['usuario_id','motivo'])


def downgrade() -> None:
    # Drop new index
    try:
        op.drop_index('ix_codigo_autenticacao_usuario_motivo', table_name=table_name)
    except Exception:
        pass

    # Recreate email column (nullable=True to avoid data issues on downgrade)
    with op.batch_alter_table(table_name) as batch_op:
        batch_op.add_column(sa.Column('email', sa.String(length=150), nullable=True))
        try:
            batch_op.create_foreign_key('codigo_autenticacao_email_fkey', 'usuario', ['email'], ['email'])
        except Exception:
            pass
        # Restore FK without cascade (best-effort)
        try:
            batch_op.drop_constraint('codigo_autenticacao_usuario_id_fkey', type_='foreignkey')
        except Exception:
            pass
        batch_op.create_foreign_key('codigo_autenticacao_usuario_id_fkey', 'usuario', ['usuario_id'], ['id'])

    # Restore old index
    try:
        op.create_index('ix_codigo_autenticacao_email_motivo', table_name, ['email','motivo'])
    except Exception:
        pass
