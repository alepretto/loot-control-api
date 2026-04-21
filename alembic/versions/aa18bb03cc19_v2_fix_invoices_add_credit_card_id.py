"""v2 fix invoices add credit_card_id column

Revision ID: aa18bb03cc19
Revises: aa17bb02cc18
Create Date: 2026-04-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa18bb03cc19"
down_revision: Union[str, None] = "aa17bb02cc18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Add credit_card_id column if not exists
    conn.execute(sa.text("""
        ALTER TABLE finance.invoices 
        ADD COLUMN IF NOT EXISTS credit_card_id UUID
    """))
    
    # Add foreign key constraint if not exists
    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE finance.invoices 
            ADD CONSTRAINT fk_invoices_credit_card_id 
            FOREIGN KEY (credit_card_id) REFERENCES finance.credit_cards(id) ON DELETE CASCADE;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))
    
    # Add index for credit_card_id
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_invoices_credit_card_id 
        ON finance.invoices (credit_card_id)
    """))
    
    # Try to migrate data from account_id to credit_card_id if account_id exists
    conn.execute(sa.text("""
        DO $$
        BEGIN
            -- Check if account_id column exists
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'finance' 
                AND table_name = 'invoices' 
                AND column_name = 'account_id'
            ) THEN
                -- Update invoices with credit_card_id based on account_id
                UPDATE finance.invoices i
                SET credit_card_id = cc.id
                FROM finance.accounts a
                INNER JOIN finance.payment_methods pm ON pm.account_id = a.id AND pm.type = 'credit'
                INNER JOIN finance.credit_cards cc ON cc.payment_method_id = pm.id
                WHERE i.account_id = a.id
                AND i.credit_card_id IS NULL;
            END IF;
        END $$;
    """))
    
    # Make credit_card_id not null if all rows have been migrated
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM finance.invoices WHERE credit_card_id IS NULL
            ) THEN
                ALTER TABLE finance.invoices ALTER COLUMN credit_card_id SET NOT NULL;
            END IF;
        END $$;
    """))
    
    # Add unique constraint for credit_card_id + reference_month
    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE finance.invoices 
            ADD CONSTRAINT uq_invoices_credit_card_month 
            UNIQUE (credit_card_id, reference_month);
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """))


def downgrade() -> None:
    conn = op.get_bind()
    
    conn.execute(sa.text("""
        ALTER TABLE finance.invoices 
        DROP CONSTRAINT IF EXISTS uq_invoices_credit_card_month
    """))
    
    conn.execute(sa.text("""
        ALTER TABLE finance.invoices 
        DROP CONSTRAINT IF EXISTS fk_invoices_credit_card_id
    """))
    
    conn.execute(sa.text("""
        DROP INDEX IF EXISTS ix_finance_invoices_credit_card_id
    """))
    
    conn.execute(sa.text("""
        ALTER TABLE finance.invoices DROP COLUMN IF EXISTS credit_card_id
    """))
