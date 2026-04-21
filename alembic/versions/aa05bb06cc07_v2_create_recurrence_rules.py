"""v2 create recurrence_rules table

Revision ID: aa05bb06cc07
Revises: aa04bb05cc06
Create Date: 2026-04-18 00:05:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa05bb06cc07"
down_revision: Union[str, None] = "aa04bb05cc06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE finance.recurrencefrequency AS ENUM
                ('daily','weekly','monthly','yearly');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS finance.recurrence_rules (
            id                   UUID        NOT NULL DEFAULT gen_random_uuid(),
            user_id              UUID        NOT NULL,
            name                 VARCHAR     NOT NULL,
            frequency            finance.recurrencefrequency NOT NULL,
            interval             INTEGER     NOT NULL DEFAULT 1,
            start_date           DATE        NOT NULL,
            end_date             DATE,
            template_transaction JSONB       NOT NULL,
            is_active            BOOLEAN     NOT NULL DEFAULT true,
            last_generated_at    TIMESTAMPTZ,
            created_at           TIMESTAMPTZ NOT NULL,
            updated_at           TIMESTAMPTZ NOT NULL,
            CONSTRAINT pk_recurrence_rules PRIMARY KEY (id),
            CONSTRAINT fk_recurrence_rules_user_id FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_recurrence_rules_user_id
        ON finance.recurrence_rules (user_id)
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS finance.recurrence_rules"))
    conn.execute(sa.text("DROP TYPE IF EXISTS finance.recurrencefrequency"))
