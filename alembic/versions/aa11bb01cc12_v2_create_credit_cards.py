"""v2 create credit_cards table

Revision ID: aa11bb01cc12
Revises: aa10bb09cc08
Create Date: 2026-04-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa11bb01cc12"
down_revision: Union[str, None] = "aa10bb09cc08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "credit_cards",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("payment_method_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("limit_amount", sa.Float(), nullable=False),
        sa.Column("due_day", sa.Integer(), nullable=False),
        sa.Column("closing_offset", sa.Integer(), server_default="3", nullable=False),
        sa.Column("current_balance", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_method_id", name="uq_credit_cards_payment_method"),
        schema="finance",
    )


def downgrade() -> None:
    op.drop_table("credit_cards", schema="finance")