"""v2 update transactions: add account_id, description, invoice_id, recurrence_id, is_recurring

Revision ID: aa06bb07cc08
Revises: aa05bb06cc07
Create Date: 2026-04-18 00:06:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa06bb07cc08"
down_revision: Union[str, None] = "aa05bb06cc07"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions ADD COLUMN IF NOT EXISTS account_id UUID
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE finance.transactions
                ADD CONSTRAINT fk_transactions_account_id
                FOREIGN KEY (account_id) REFERENCES finance.accounts(id) ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_transactions_account_id
        ON finance.transactions (account_id)
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions ADD COLUMN IF NOT EXISTS description VARCHAR
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions ADD COLUMN IF NOT EXISTS invoice_id UUID
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE finance.transactions
                ADD CONSTRAINT fk_transactions_invoice_id
                FOREIGN KEY (invoice_id) REFERENCES finance.invoices(id) ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_transactions_invoice_id
        ON finance.transactions (invoice_id)
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions ADD COLUMN IF NOT EXISTS recurrence_id UUID
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE finance.transactions
                ADD CONSTRAINT fk_transactions_recurrence_id
                FOREIGN KEY (recurrence_id) REFERENCES finance.recurrence_rules(id)
                ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_transactions_recurrence_id
        ON finance.transactions (recurrence_id)
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions
            ADD COLUMN IF NOT EXISTS is_recurring BOOLEAN NOT NULL DEFAULT false
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions DROP COLUMN IF EXISTS is_recurring
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions DROP CONSTRAINT IF EXISTS fk_transactions_recurrence_id
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions DROP COLUMN IF EXISTS recurrence_id
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions DROP CONSTRAINT IF EXISTS fk_transactions_invoice_id
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions DROP COLUMN IF EXISTS invoice_id
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions DROP COLUMN IF EXISTS description
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions DROP CONSTRAINT IF EXISTS fk_transactions_account_id
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions DROP COLUMN IF EXISTS account_id
    """))
