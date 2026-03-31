"""add payment_methods table and payment_method_id to transactions

Revision ID: a6b7c8d9e0f1
Revises: f4a5b6c1d2e3
Create Date: 2026-03-30 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a6b7c8d9e0f1"
down_revision: Union[str, None] = "a5b6c1d2e3f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ENUM_NAME = "paymentmethodcategory"
_TABLE = "payment_methods"
_SCHEMA = "finance"


def _table_exists(conn, table: str, schema: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = :schema AND table_name = :table"
        ),
        {"schema": schema, "table": table},
    )
    return result.first() is not None


def _column_exists(conn, table: str, column: str, schema: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = :schema AND table_name = :table AND column_name = :col"
        ),
        {"schema": schema, "table": table, "col": column},
    )
    return result.first() is not None


def _enum_exists(conn, name: str, schema: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_type t "
            "JOIN pg_namespace n ON n.oid = t.typnamespace "
            "WHERE t.typname = :name AND n.nspname = :schema"
        ),
        {"name": name, "schema": schema},
    )
    return result.first() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Criar o tipo ENUM
    if not _enum_exists(conn, _ENUM_NAME, _SCHEMA):
        sa.Enum("money", "benefit", name=_ENUM_NAME, schema=_SCHEMA).create(conn)

    # 2. Criar tabela finance.payment_methods
    if not _table_exists(conn, _TABLE, _SCHEMA):
        op.create_table(
            _TABLE,
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.Uuid(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column(
                "category",
                sa.Enum("money", "benefit", name=_ENUM_NAME, schema=_SCHEMA, create_type=False),
                nullable=False,
            ),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_payment_methods_user_id"),
            sa.UniqueConstraint("user_id", "name", name="uq_payment_methods_user_name"),
            sa.PrimaryKeyConstraint("id"),
            schema=_SCHEMA,
        )
        op.create_index(
            "ix_finance_payment_methods_user_id",
            _TABLE,
            ["user_id"],
            schema=_SCHEMA,
        )

    # 3. Adicionar coluna payment_method_id em transactions (nullable)
    if not _column_exists(conn, "transactions", "payment_method_id", _SCHEMA):
        op.add_column(
            "transactions",
            sa.Column("payment_method_id", sa.Uuid(), nullable=True),
            schema=_SCHEMA,
        )
        op.create_foreign_key(
            "fk_transactions_payment_method_id",
            "transactions",
            _TABLE,
            ["payment_method_id"],
            ["id"],
            source_schema=_SCHEMA,
            referent_schema=_SCHEMA,
            ondelete="SET NULL",
        )
        op.create_index(
            "ix_finance_transactions_payment_method_id",
            "transactions",
            ["payment_method_id"],
            schema=_SCHEMA,
        )


def downgrade() -> None:
    conn = op.get_bind()

    if _column_exists(conn, "transactions", "payment_method_id", _SCHEMA):
        op.drop_index(
            "ix_finance_transactions_payment_method_id",
            table_name="transactions",
            schema=_SCHEMA,
        )
        op.drop_constraint(
            "fk_transactions_payment_method_id",
            "transactions",
            schema=_SCHEMA,
            type_="foreignkey",
        )
        op.drop_column("transactions", "payment_method_id", schema=_SCHEMA)

    if _table_exists(conn, _TABLE, _SCHEMA):
        op.drop_index("ix_finance_payment_methods_user_id", table_name=_TABLE, schema=_SCHEMA)
        op.drop_table(_TABLE, schema=_SCHEMA)

    if _enum_exists(conn, _ENUM_NAME, _SCHEMA):
        sa.Enum(name=_ENUM_NAME, schema=_SCHEMA).drop(conn)
