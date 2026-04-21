"""v2 create liabilities table

Revision ID: aa07bb08cc09
Revises: aa06bb07cc08
Create Date: 2026-04-18 00:07:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa07bb08cc09"
down_revision: Union[str, None] = "aa06bb07cc08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE finance.liabilitytype AS ENUM ('financing','loan','other');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE finance.liabilityindex AS ENUM ('CDI','IPCA','fixed','none');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS finance.liabilities (
            id                  UUID        NOT NULL DEFAULT gen_random_uuid(),
            user_id             UUID        NOT NULL,
            name                VARCHAR     NOT NULL,
            type                finance.liabilitytype NOT NULL,
            institution         VARCHAR,
            total_value         NUMERIC     NOT NULL,
            outstanding_balance NUMERIC     NOT NULL,
            monthly_payment     NUMERIC,
            start_date          DATE,
            end_date            DATE,
            interest_rate       NUMERIC,
            index               finance.liabilityindex,
            is_active           BOOLEAN     NOT NULL DEFAULT true,
            created_at          TIMESTAMPTZ NOT NULL,
            updated_at          TIMESTAMPTZ NOT NULL,
            CONSTRAINT pk_liabilities PRIMARY KEY (id),
            CONSTRAINT fk_liabilities_user_id FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_liabilities_user_id
        ON finance.liabilities (user_id)
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS finance.liabilities"))
    conn.execute(sa.text("DROP TYPE IF EXISTS finance.liabilityindex"))
    conn.execute(sa.text("DROP TYPE IF EXISTS finance.liabilitytype"))
