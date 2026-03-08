"""move type from categories to tags

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a1
Create Date: 2026-03-08 03:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'b2c3d4e5f6a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ENUM = sa.Enum("outcome", "income", name="categorytype", schema="finance")


def upgrade() -> None:
    # 1. Adiciona type em tags (nullable inicialmente para poder popular)
    op.add_column(
        "tags",
        sa.Column("type", _ENUM, nullable=True),
        schema="finance",
    )

    # 2. Migra type de categories → tags via JOIN
    op.execute("""
        UPDATE finance.tags t
        SET type = c.type
        FROM finance.categories c
        WHERE c.id = t.category_id
    """)

    # 3. Torna NOT NULL
    op.alter_column("tags", "type", nullable=False, schema="finance")

    # 4. Remove type de categories
    op.drop_column("categories", "type", schema="finance")


def downgrade() -> None:
    # 1. Devolve type para categories (nullable primeiro)
    op.add_column(
        "categories",
        sa.Column("type", _ENUM, nullable=True),
        schema="finance",
    )

    # 2. Inferir tipo majoritário da categoria a partir das tags
    op.execute("""
        UPDATE finance.categories c
        SET type = (
            SELECT t.type
            FROM finance.tags t
            WHERE t.category_id = c.id
            GROUP BY t.type
            ORDER BY COUNT(*) DESC
            LIMIT 1
        )
    """)

    # 3. Categorias sem tags: default outcome
    op.execute("""
        UPDATE finance.categories SET type = 'outcome' WHERE type IS NULL
    """)

    op.alter_column("categories", "type", nullable=False, schema="finance")

    # 4. Remove type de tags
    op.drop_column("tags", "type", schema="finance")
