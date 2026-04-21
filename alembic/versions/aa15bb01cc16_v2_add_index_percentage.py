"""v2 add index_percentage to transactions

Revision ID: aa15bb01cc16
Revises: aa14bb01cc15
Create Date: 2026-04-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa15bb01cc16"
down_revision: Union[str, None] = "aa14bb01cc15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions 
        ADD COLUMN IF NOT EXISTS index_percentage FLOAT
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions 
        DROP COLUMN IF EXISTS index_percentage
    """))