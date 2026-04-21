"""v2 extend accounttype enum with wallet, benefit

Revision ID: aa16bb01cc17
Revises: aa15bb01cc16
Create Date: 2026-04-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa16bb01cc17"
down_revision: Union[str, None] = "aa15bb01cc16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TYPE finance.accounttype ADD VALUE IF NOT EXISTS 'wallet'"))
    conn.execute(sa.text("ALTER TYPE finance.accounttype ADD VALUE IF NOT EXISTS 'benefit'"))


def downgrade() -> None:
    pass
