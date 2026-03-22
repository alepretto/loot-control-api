"""add composite index on transactions (user_id, date_transaction)

Revision ID: a5b6c1d2e3f4
Revises: f4a5b6c1d2e3
Create Date: 2026-03-21 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a5b6c1d2e3f4"
down_revision: Union[str, None] = "f4a5b6c1d2e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "ix_transactions_user_id_date_transaction"


def upgrade() -> None:
    conn = op.get_bind()
    exists = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_indexes WHERE schemaname = 'finance' AND indexname = :name"
        ),
        {"name": INDEX_NAME},
    ).scalar()

    if not exists:
        op.create_index(
            INDEX_NAME,
            "transactions",
            ["user_id", "date_transaction"],
            schema="finance",
        )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name="transactions", schema="finance")
