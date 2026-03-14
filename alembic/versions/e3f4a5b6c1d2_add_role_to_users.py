"""add role to users

Revision ID: e3f4a5b6c1d2
Revises: d2e3f4a5b6c1
Create Date: 2026-03-08 05:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e3f4a5b6c1d2"
down_revision: Union[str, None] = "d2e3f4a5b6c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("users")]
    if "role" not in columns:
        op.add_column("users", sa.Column("role", sa.String(), nullable=False, server_default="user"))


def downgrade() -> None:
    op.drop_column("users", "role")
