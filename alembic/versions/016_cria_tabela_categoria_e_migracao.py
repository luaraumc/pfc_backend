"""cria tabela categoria e migra coluna categoria de habilidade para categoria_id

Revision ID: 016_cria_tabela_categoria_e_migracao
Revises: 015_seed_normalizacao_from_const
Create Date: 2025-10-17
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '016_cria_tabela_categoria_e_migracao'
down_revision = '015_seed_normalizacao_from_const'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Criar tabela categoria
    op.create_table(
        'categoria',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('nome', sa.String(length=150), nullable=False, unique=True),
        sa.Column('atualizado_em', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    )

    # 2) Adicionar coluna categoria_id (inicialmente nullable para migração)
    with op.batch_alter_table('habilidade') as batch_op:
        batch_op.add_column(sa.Column('categoria_id', sa.Integer(), nullable=True))

    # 3) Popular tabela categoria e atualizar habilidade.categoria_id
    bind = op.get_bind()
    conn = bind.connect()

    # Obter categorias distintas existentes
    res = conn.execute(sa.text("SELECT DISTINCT categoria FROM habilidade"))
    categorias = [row[0] for row in res if row[0] is not None]

    # Inserir categorias e mapear ids
    nome_to_id = {}
    for nome in categorias:
        # ignora espaços excedentes
        nome_pad = nome.strip()
        if not nome_pad:
            continue
        # inserir se não existir
        insert_stmt = sa.text(
            "INSERT INTO categoria (nome) VALUES (:nome) ON CONFLICT (nome) DO UPDATE SET nome = EXCLUDED.nome RETURNING id"
        )
        new_id = conn.execute(insert_stmt, {"nome": nome_pad}).scalar()
        nome_to_id[nome] = new_id

    # Garantir existência de categoria 'Ferramentas' para nulos/invalidos
    ferramentas_id = conn.execute(
        sa.text(
            "INSERT INTO categoria (nome) VALUES (:nome) ON CONFLICT (nome) DO UPDATE SET nome = EXCLUDED.nome RETURNING id"
        ),
        {"nome": "Ferramentas"},
    ).scalar()

    # Atualizar cada habilidade com categoria_id correspondente
    # Valores nulos ou vazios irão para 'Ferramentas'
    update_stmt = sa.text(
        """
        UPDATE habilidade h
        SET categoria_id = COALESCE(
            (
                SELECT c.id FROM categoria c WHERE c.nome = h.categoria
            ), :ferramentas_id
        )
        """
    )
    conn.execute(update_stmt, {"ferramentas_id": ferramentas_id})

    # 4) Tornar NOT NULL e adicionar FK
    with op.batch_alter_table('habilidade') as batch_op:
        batch_op.alter_column('categoria_id', nullable=False)
        batch_op.create_foreign_key(
            'fk_habilidade_categoria', 'categoria', ['categoria_id'], ['id'], ondelete='RESTRICT'
        )
        # Remover coluna antiga de string
        batch_op.drop_column('categoria')


def downgrade() -> None:
    # Recriar coluna antiga de categoria como string
    with op.batch_alter_table('habilidade') as batch_op:
        batch_op.add_column(sa.Column('categoria', sa.String(length=120), nullable=False, server_default='Ferramentas'))

    bind = op.get_bind()
    conn = bind.connect()

    # Preencher a coluna antiga com o nome da categoria
    conn.execute(sa.text(
        """
        UPDATE habilidade h
        SET categoria = (
            SELECT c.nome FROM categoria c WHERE c.id = h.categoria_id
        )
        """
    ))

    # Remover FK e coluna categoria_id
    with op.batch_alter_table('habilidade') as batch_op:
        batch_op.drop_constraint('fk_habilidade_categoria', type_='foreignkey')
        batch_op.drop_column('categoria_id')

    # Remover tabela categoria
    op.drop_table('categoria')
