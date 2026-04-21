"""v2 create net_worth_snapshots table

Revision ID: aa09bb10cc11
Revises: aa08bb09cc10
Create Date: 2026-04-18 00:09:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa09bb10cc11"
down_revision: Union[str, None] = "aa08bb09cc10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS finance.net_worth_snapshots (
            id                   UUID    NOT NULL DEFAULT gen_random_uuid(),
            user_id              UUID    NOT NULL,
            date                 DATE    NOT NULL,
            financial_assets     NUMERIC NOT NULL,
            investment_assets    NUMERIC NOT NULL,
            liabilities_credit   NUMERIC NOT NULL,
            liabilities_long_term NUMERIC NOT NULL,
            net_worth            NUMERIC NOT NULL,
            created_at           TIMESTAMPTZ NOT NULL,
            CONSTRAINT pk_net_worth_snapshots PRIMARY KEY (id),
            CONSTRAINT uq_net_worth_snapshots_user_date UNIQUE (user_id, date),
            CONSTRAINT fk_net_worth_snapshots_user_id FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_net_worth_snapshots_user_id
        ON finance.net_worth_snapshots (user_id)
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS finance.net_worth_snapshots"))
