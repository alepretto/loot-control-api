"""v2 fix payment_methods unique constraint to include account_id

Revision ID: aa17bb02cc18
Revises: aa16bb01cc17
Create Date: 2026-04-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa17bb02cc18"
down_revision: Union[str, None] = "aa16bb01cc17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Drop old unique constraint
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods 
        DROP CONSTRAINT IF EXISTS uq_payment_methods_user_name
    """))
    
    # Add new unique constraint on (user_id, account_id, name)
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods 
        ADD CONSTRAINT uq_payment_methods_user_account_name 
        UNIQUE (user_id, account_id, name)
    """))


def downgrade() -> None:
    conn = op.get_bind()
    
    # Drop new constraint
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods 
        DROP CONSTRAINT IF EXISTS uq_payment_methods_user_account_name
    """))
    
    # Restore old constraint
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods 
        ADD CONSTRAINT uq_payment_methods_user_name 
        UNIQUE (user_id, name)
    """))
