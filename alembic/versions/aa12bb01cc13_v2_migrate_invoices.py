"""v2 migrate invoices to credit_card_id

Revision ID: aa12bb01cc13
Revises: aa11bb01cc12
Create Date: 2026-04-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa12bb01cc13"
down_revision: Union[str, None] = "aa11bb01cc12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("""
        ALTER TABLE finance.invoices 
        ADD COLUMN IF NOT EXISTS credit_card_id UUID REFERENCES finance.credit_cards(id) ON DELETE CASCADE
    """))

    conn.execute(sa.text("""
        UPDATE finance.invoices 
        SET credit_card_id = subq.new_credit_card_id
        FROM (
            SELECT i.id as invoice_id, cc.id as new_credit_card_id
            FROM finance.invoices i
            INNER JOIN finance.accounts a ON i.account_id = a.id
            INNER JOIN finance.payment_methods pm ON pm.account_id = a.id AND pm.type = 'credit'
            INNER JOIN finance.credit_cards cc ON cc.payment_method_id = pm.id
        ) subq
        WHERE finance.invoices.id = subq.invoice_id
    """))

    conn.execute(sa.text("""
        ALTER TABLE finance.invoices ALTER COLUMN credit_card_id SET NOT NULL
    """))

    conn.execute(sa.text("""
        ALTER TABLE finance.invoices DROP CONSTRAINT IF EXISTS uq_invoices_account_month
    """))

    conn.execute(sa.text("""
        ALTER TABLE finance.invoices 
        ADD CONSTRAINT uq_invoices_credit_card_month 
        UNIQUE (credit_card_id, reference_month)
    """))

    conn.execute(sa.text("""
        ALTER TABLE finance.invoices DROP COLUMN IF EXISTS account_id
    """))


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("""
        ALTER TABLE finance.invoices ADD COLUMN account_id UUID REFERENCES finance.accounts(id) ON DELETE CASCADE
    """))

    conn.execute(sa.text("""
        UPDATE finance.invoices SET account_id = subq.account_id
        FROM (
            SELECT i.id as invoice_id, cc.payment_method_id as pm_id, pm.account_id
            FROM finance.invoices i
            INNER JOIN finance.credit_cards cc ON i.credit_card_id = cc.id
            INNER JOIN finance.payment_methods pm ON cc.payment_method_id = pm.id
        ) subq
        WHERE finance.invoices.id = subq.invoice_id
    """))

    conn.execute(sa.text("""
        ALTER TABLE finance.invoices ALTER COLUMN account_id SET NOT NULL
    """))

    conn.execute(sa.text("""
        ALTER TABLE finance.invoices DROP CONSTRAINT IF EXISTS uq_invoices_credit_card_month
    """))

    conn.execute(sa.text("""
        ALTER TABLE finance.invoices 
        ADD CONSTRAINT uq_invoices_account_month 
        UNIQUE (account_id, reference_month)
    """))

    conn.execute(sa.text("""
        ALTER TABLE finance.invoices DROP COLUMN IF EXISTS credit_card_id
    """))