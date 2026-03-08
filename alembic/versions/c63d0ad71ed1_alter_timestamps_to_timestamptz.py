"""alter timestamps to timestamptz

Revision ID: c63d0ad71ed1
Revises: 1f79f8390a33
Create Date: 2026-03-08 01:44:11.042557

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c63d0ad71ed1'
down_revision: Union[str, None] = '1f79f8390a33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = [
    ("users", None),
    ("categories", "finance"),
    ("tags", "finance"),
    ("transactions", "finance"),
]


def upgrade() -> None:
    for table, schema in _TABLES:
        kwargs = {"schema": schema} if schema else {}
        for col in ("created_at", "updated_at"):
            op.alter_column(
                table,
                col,
                existing_type=sa.DateTime(),
                type_=sa.DateTime(timezone=True),
                existing_nullable=False,
                postgresql_using=f"{col} AT TIME ZONE 'UTC'",
                **kwargs,
            )


def downgrade() -> None:
    for table, schema in _TABLES:
        kwargs = {"schema": schema} if schema else {}
        for col in ("created_at", "updated_at"):
            op.alter_column(
                table,
                col,
                existing_type=sa.DateTime(timezone=True),
                type_=sa.DateTime(),
                existing_nullable=False,
                postgresql_using=f"{col} AT TIME ZONE 'UTC'",
                **kwargs,
            )
