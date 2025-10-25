"""seed categorias na tabela categoria

Revision ID: 017_seed_categorias
Revises: 016_cria_tabela_categoria_e_migracao
Create Date: 2025-10-17
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '017_seed_categorias'
down_revision = '016_cria_tabela_categoria'
branch_labels = None
depends_on = None


CATEGORIAS = [
    "Aplicações de Negócio",
    "Arquitetura",
    "Backend",
    "Banco de Dados",
    "Bibliotecas/SDKs",
    "Cloud",
    "Compliance",
    "Conceitos",
    "Dados",
    "Desenvolvimento",
    "DevOps",
    "Ferramentas",
    "Governança e Gestão",
    "IA/ML",
    "Identidade",
    "Identidade/MDM",
    "Infraestrutura",
    "ITSM",
    "Linguagens e formatos",
    "Mensageria",
    "Modelos de Entrega",
    "Observabilidade",
    "Produtividade",
    "Qualidade",
    "Redes",
    "Segurança",
    "Sistemas Operacionais",
    "Web",
]


def upgrade() -> None:
    conn = op.get_bind()
    insert_stmt = sa.text(
        "INSERT INTO categoria (nome) VALUES (:nome) ON CONFLICT (nome) DO NOTHING"
    )
    for nome in CATEGORIAS:
        conn.execute(insert_stmt, {"nome": nome})


def downgrade() -> None:
    conn = op.get_bind()
    # Remove somente categorias que não estejam em uso por habilidades
    delete_stmt = sa.text(
        """
        DELETE FROM categoria c
        WHERE c.nome = :nome
          AND NOT EXISTS (
              SELECT 1 FROM habilidade h WHERE h.categoria_id = c.id
          )
        """
    )
    for nome in CATEGORIAS:
        conn.execute(delete_stmt, {"nome": nome})
