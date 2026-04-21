"""v2 refactor payment_methods: category->type (debit|credit|benefit), add account_id

Revision ID: aa02bb03cc04
Revises: aa01bb02cc03
Create Date: 2026-04-18 00:02:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa02bb03cc04"
down_revision: Union[str, None] = "aa01bb02cc03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE finance.paymentmethodtype AS ENUM ('debit','credit','benefit');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    # add type column (nullable first), migrate, set not null, drop old column
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods
            ADD COLUMN IF NOT EXISTS type finance.paymentmethodtype
    """))
    conn.execute(sa.text("""
        UPDATE finance.payment_methods
        SET type = CASE
            WHEN category = 'money' THEN 'debit'::finance.paymentmethodtype
            ELSE 'benefit'::finance.paymentmethodtype
        END
        WHERE type IS NULL
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods
            ALTER COLUMN type SET NOT NULL
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods
            DROP COLUMN IF EXISTS category
    """))
    conn.execute(sa.text("DROP TYPE IF EXISTS finance.paymentmethodcategory"))
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods
            ADD COLUMN IF NOT EXISTS account_id UUID
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE finance.payment_methods
                ADD CONSTRAINT fk_payment_methods_account_id
                FOREIGN KEY (account_id) REFERENCES finance.accounts(id) ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_payment_methods_account_id
        ON finance.payment_methods (account_id)
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods
            DROP CONSTRAINT IF EXISTS fk_payment_methods_account_id
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods DROP COLUMN IF EXISTS account_id
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE finance.paymentmethodcategory AS ENUM ('money','benefit');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods
            ADD COLUMN IF NOT EXISTS category finance.paymentmethodcategory
    """))
    conn.execute(sa.text("""
        UPDATE finance.payment_methods
        SET category = CASE
            WHEN type = 'debit' THEN 'money'::finance.paymentmethodcategory
            ELSE 'benefit'::finance.paymentmethodcategory
        END
        WHERE category IS NULL
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods
            ALTER COLUMN category SET NOT NULL
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.payment_methods DROP COLUMN IF EXISTS type
    """))
    conn.execute(sa.text("DROP TYPE IF EXISTS finance.paymentmethodtype"))
