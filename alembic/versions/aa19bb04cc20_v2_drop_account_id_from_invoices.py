"""v2 drop account_id from invoices

Revision ID: aa19bb04cc20
Revises: aa18bb03cc19
Create Date: 2026-04-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa19bb04cc20"
down_revision: Union[str, None] = "aa18bb03cc19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Drop foreign key constraint on account_id if exists
    conn.execute(sa.text("""
        ALTER TABLE finance.invoices 
        DROP CONSTRAINT IF EXISTS fk_invoices_account_id
    """))
    
    # Drop index on account_id if exists
    conn.execute(sa.text("""
        DROP INDEX IF EXISTS ix_finance_invoices_account_id
    """))
    
    # Drop unique constraint on account_id + reference_month if exists
    conn.execute(sa.text("""
        ALTER TABLE finance.invoices 
        DROP CONSTRAINT IF EXISTS uq_invoices_account_month
    """))
    
    # Drop account_id column if exists
    conn.execute(sa.text("""
        ALTER TABLE finance.invoices DROP COLUMN IF EXISTS account_id
    """))
    
    # Ensure credit_card_id is not null if it has data
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'finance' 
                AND table_name = 'invoices' 
                AND column_name = 'credit_card_id'
            ) AND NOT EXISTS (
                SELECT 1 FROM finance.invoices WHERE credit_card_id IS NULL
            ) THEN
                ALTER TABLE finance.invoices ALTER COLUMN credit_card_id SET NOT NULL;
            END IF;
        END $$;
    """))


def downgrade() -> None:
    conn = op.get_bind()
    
    # Add account_id column back
    conn.execute(sa.text("""
        ALTER TABLE finance.invoices 
        ADD COLUMN IF NOT EXISTS account_id UUID REFERENCES finance.accounts(id) ON DELETE CASCADE
    """))
    
    # Add foreign key constraint
    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE finance.invoices 
            ADD CONSTRAINT fk_invoices_account_id 
            FOREIGN KEY (account_id) REFERENCES finance.accounts(id) ON DELETE CASCADE;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))
    
    # Add index
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_invoices_account_id 
        ON finance.invoices (account_id)
    """))
    
    # Add unique constraint
    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE finance.invoices 
            ADD CONSTRAINT uq_invoices_account_month 
            UNIQUE (account_id, reference_month);
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))
    
    # Try to populate account_id from credit_card_id data
    conn.execute(sa.text("""
        UPDATE finance.invoices i
        SET account_id = subq.account_id
        FROM (
            SELECT inv.id as invoice_id, pm.account_id
            FROM finance.invoices inv
            INNER JOIN finance.credit_cards cc ON inv.credit_card_id = cc.id
            INNER JOIN finance.payment_methods pm ON cc.payment_method_id = pm.id
        ) subq
        WHERE i.id = subq.invoice_id
        AND i.account_id IS NULL
    """))
