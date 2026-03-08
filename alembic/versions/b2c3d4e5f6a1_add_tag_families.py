"""add tag_families table and family_id FK on categories

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-03-08 02:05:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = 'b2c3d4e5f6a1'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names(schema="finance"))

    # Cria tag_families apenas se não existir (pode ter sido criada via create_all)
    if "tag_families" not in existing_tables:
        op.create_table(
            "tag_families",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            schema="finance",
        )
        op.create_index(
            op.f("ix_finance_tag_families_user_id"),
            "tag_families",
            ["user_id"],
            unique=False,
            schema="finance",
        )

    # Adiciona family_id em categories apenas se não existir
    existing_cols = {c["name"] for c in inspector.get_columns("categories", schema="finance")}
    if "family_id" not in existing_cols:
        op.add_column(
            "categories",
            sa.Column("family_id", sa.Uuid(), nullable=True),
            schema="finance",
        )
        op.create_index(
            op.f("ix_finance_categories_family_id"),
            "categories",
            ["family_id"],
            unique=False,
            schema="finance",
        )
        op.create_foreign_key(
            "fk_categories_family_id",
            "categories",
            "tag_families",
            ["family_id"],
            ["id"],
            source_schema="finance",
            referent_schema="finance",
            ondelete="SET NULL",
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    existing_cols = {c["name"] for c in inspector.get_columns("categories", schema="finance")}
    if "family_id" in existing_cols:
        op.drop_constraint(
            "fk_categories_family_id",
            "categories",
            schema="finance",
            type_="foreignkey",
        )
        op.drop_index(
            op.f("ix_finance_categories_family_id"),
            table_name="categories",
            schema="finance",
        )
        op.drop_column("categories", "family_id", schema="finance")

    existing_tables = set(inspector.get_table_names(schema="finance"))
    if "tag_families" in existing_tables:
        op.drop_index(
            op.f("ix_finance_tag_families_user_id"),
            table_name="tag_families",
            schema="finance",
        )
        op.drop_table("tag_families", schema="finance")
