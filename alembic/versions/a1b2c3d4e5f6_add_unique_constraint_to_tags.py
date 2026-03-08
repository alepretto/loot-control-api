"""add unique constraint to tags (user_id, category_id, name)

Revision ID: a1b2c3d4e5f6
Revises: c63d0ad71ed1
Create Date: 2026-03-08 02:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c63d0ad71ed1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    constraints = {c["name"] for c in inspector.get_unique_constraints("tags", schema="finance")}
    if "uq_tags_user_category_name" not in constraints:
        op.create_unique_constraint(
            "uq_tags_user_category_name",
            "tags",
            ["user_id", "category_id", "name"],
            schema="finance",
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    constraints = {c["name"] for c in inspector.get_unique_constraints("tags", schema="finance")}
    if "uq_tags_user_category_name" in constraints:
        op.drop_constraint(
            "uq_tags_user_category_name",
            "tags",
            schema="finance",
        )
