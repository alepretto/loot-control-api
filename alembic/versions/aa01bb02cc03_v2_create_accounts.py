"""v2 create accounts table

Revision ID: aa01bb02cc03
Revises: a6b7c8d9e0f1
Create Date: 2026-04-18 00:01:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa01bb02cc03"
down_revision: Union[str, None] = "a6b7c8d9e0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE finance.accounttype AS ENUM
                ('checking','savings','broker','digital','credit_card');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE finance.balancemode AS ENUM ('calculated','manual');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS finance.accounts (
            id          UUID        NOT NULL DEFAULT gen_random_uuid(),
            user_id     UUID        NOT NULL,
            name        VARCHAR     NOT NULL,
            type        finance.accounttype  NOT NULL,
            institution VARCHAR,
            currency    finance.currencies   NOT NULL DEFAULT 'BRL',
            balance_mode finance.balancemode NOT NULL DEFAULT 'calculated',
            manual_balance  NUMERIC,
            credit_limit    NUMERIC,
            closing_day     INTEGER,
            due_day         INTEGER,
            is_active   BOOLEAN     NOT NULL DEFAULT true,
            created_at  TIMESTAMPTZ NOT NULL,
            updated_at  TIMESTAMPTZ NOT NULL,
            CONSTRAINT pk_accounts PRIMARY KEY (id),
            CONSTRAINT uq_accounts_user_name UNIQUE (user_id, name),
            CONSTRAINT fk_accounts_user_id FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_accounts_user_id
        ON finance.accounts (user_id)
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS finance.accounts"))
    conn.execute(sa.text("DROP TYPE IF EXISTS finance.balancemode"))
    conn.execute(sa.text("DROP TYPE IF EXISTS finance.accounttype"))
