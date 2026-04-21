"""v2 migrate credit_card accounts to credit_cards table

Revision ID: aa14bb01cc15
Revises: aa13bb01cc14
Create Date: 2026-04-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa14bb01cc15"
down_revision: Union[str, None] = "aa13bb01cc14"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    conn.execute(sa.text("""
        INSERT INTO finance.payment_methods (id, user_id, name, type, account_id, is_active, created_at, updated_at)
        SELECT 
            gen_random_uuid(),
            user_id,
            name || ' - Crédito',
            'credit'::finance.paymentmethodtype,
            id,
            is_active,
            created_at,
            updated_at
        FROM finance.accounts
        WHERE type = 'credit_card'
        ON CONFLICT DO NOTHING
    """))
    
    pm_count = conn.execute(sa.text("SELECT COUNT(*) FROM finance.payment_methods WHERE type = 'credit'")).scalar()
    print(f"PaymentMethods de crédito criados: {pm_count}")
    
    conn.execute(sa.text("""
        INSERT INTO finance.credit_cards (id, payment_method_id, user_id, name, limit_amount, due_day, closing_offset, current_balance, is_active, created_at, updated_at)
        SELECT 
            gen_random_uuid(),
            pm.id,
            a.user_id,
            a.name,
            COALESCE(a.credit_limit, 0),
            COALESCE(a.due_day, 10),
            COALESCE(a.closing_day, 3),
            0,
            a.is_active,
            a.created_at,
            a.updated_at
        FROM finance.accounts a
        INNER JOIN finance.payment_methods pm ON pm.account_id = a.id AND pm.type = 'credit'
        WHERE a.type = 'credit_card'
        ON CONFLICT DO NOTHING
    """))
    
    cc_count = conn.execute(sa.text("SELECT COUNT(*) FROM finance.credit_cards")).scalar()
    print(f"CreditCards criados: {cc_count}")


def downgrade() -> None:
    conn = op.get_bind()
    print(" downgrade: reverter migração de credit_cards requer recuperação manual dos dados")