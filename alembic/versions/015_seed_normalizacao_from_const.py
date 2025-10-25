"""seed da tabela normalizacao a partir do PADROES em extracao.py

Revision ID: 015_seed_normalizacao_from_const
Revises: 014_cria_tabela_normalizacao
Create Date: 2025-10-16
"""

from alembic import op
import sqlalchemy as sa
import os, sys

# revision identifiers, used by Alembic.
revision = '015_seed_normalizacao_from_const'
down_revision = '014_cria_tabela_normalizacao'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Garante que o pacote 'app' esteja importável nas execuções do Alembic
    try:
        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        if project_root not in sys.path:
            sys.path.append(project_root)
    except Exception:
        pass
    bind = op.get_bind()
    meta = sa.MetaData()
    normalizacao = sa.Table(
        'normalizacao',
        meta,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('nome', sa.String(200), nullable=False),
        sa.Column('nome_padronizado', sa.String(150), nullable=False),
    )
    try:
        # Importa o dicionário PADROES vigente para popular a tabela
        from app.services.extracao import PADROES  # deve existir neste momento
    except Exception as exc:
        PADROES = {}
    rows = [
        {"nome": patt, "nome_padronizado": val}
        for patt, val in (PADROES.items() if isinstance(PADROES, dict) else [])
    ]
    if rows:
        # Evita duplicados: insere apenas os que não existem
        existing = set(
            r[0]
            for r in bind.execute(sa.text("SELECT nome FROM normalizacao")).fetchall()
        )
        rows_to_insert = [r for r in rows if r["nome"] not in existing]
        if rows_to_insert:
            op.bulk_insert(normalizacao, rows_to_insert)


def downgrade() -> None:
    # Garante que o pacote 'app' esteja importável nas execuções do Alembic
    try:
        current_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        if project_root not in sys.path:
            sys.path.append(project_root)
    except Exception:
        pass
    bind = op.get_bind()
    try:
        from app.services.extracao import PADROES
    except Exception:
        PADROES = {}
    if isinstance(PADROES, dict) and PADROES:
        stmt = sa.text("DELETE FROM normalizacao WHERE nome = :nome")
        for nome in PADROES.keys():
            bind.execute(stmt, {"nome": nome})
