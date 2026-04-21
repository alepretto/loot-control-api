"""v2 create invoices table

Revision ID: aa04bb05cc06
Revises: aa03bb04cc05
Create Date: 2026-04-18 00:04:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa04bb05cc06"
down_revision: Union[str, None] = "aa03bb04cc05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE finance.invoicestatus AS ENUM ('open','closed','paid');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS finance.invoices (
            id              UUID        NOT NULL DEFAULT gen_random_uuid(),
            user_id         UUID        NOT NULL,
            account_id      UUID        NOT NULL,
            reference_month VARCHAR(7)  NOT NULL,
            closing_date    DATE        NOT NULL,
            due_date        DATE        NOT NULL,
            total_amount    NUMERIC     NOT NULL DEFAULT 0,
            status          finance.invoicestatus NOT NULL DEFAULT 'open',
            paid_at         TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL,
            updated_at      TIMESTAMPTZ NOT NULL,
            CONSTRAINT pk_invoices PRIMARY KEY (id),
            CONSTRAINT uq_invoices_account_month UNIQUE (account_id, reference_month),
            CONSTRAINT fk_invoices_user_id FOREIGN KEY (user_id) REFERENCES users(id),
            CONSTRAINT fk_invoices_account_id FOREIGN KEY (account_id)
                REFERENCES finance.accounts(id) ON DELETE CASCADE
        )
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_invoices_user_id ON finance.invoices (user_id)
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_invoices_account_id ON finance.invoices (account_id)
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS finance.invoices"))
    conn.execute(sa.text("DROP TYPE IF EXISTS finance.invoicestatus"))
