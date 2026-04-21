"""v2 payment_methods account_id not null

Revision ID: aa13bb01cc14
Revises: aa12bb01cc13
Create Date: 2026-04-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa13bb01cc14"
down_revision: Union[str, None] = "aa12bb01cc13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    conn.execute(sa.text("""
        UPDATE finance.payment_methods pm
        SET account_id = (
            SELECT a.id 
            FROM finance.accounts a 
            WHERE a.user_id = pm.user_id 
            AND a.type = 'checking'
            LIMIT 1
        )
        WHERE pm.account_id IS NULL
    """))
    
    null_count = conn.execute(sa.text("SELECT COUNT(*) FROM finance.payment_methods WHERE account_id IS NULL")).scalar()
    print(f"PaymentMethods sem account_id após migração: {null_count}")
    
    if null_count > 0:
        print("AVISO: Ainda existem payment_methods sem account_id. eles precisam ser criados manualmente.")
    
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods 
        ALTER COLUMN account_id SET NOT NULL
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods 
        ALTER COLUMN account_id DROP NOT NULL
    """))