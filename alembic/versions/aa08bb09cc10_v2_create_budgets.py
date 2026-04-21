"""v2 create budgets table

Revision ID: aa08bb09cc10
Revises: aa07bb08cc09
Create Date: 2026-04-18 00:08:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa08bb09cc10"
down_revision: Union[str, None] = "aa07bb08cc09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE finance.budgetperiod AS ENUM ('monthly','yearly');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS finance.budgets (
            id          UUID        NOT NULL DEFAULT gen_random_uuid(),
            user_id     UUID        NOT NULL,
            family_id   UUID,
            category_id UUID,
            amount      NUMERIC     NOT NULL,
            currency    finance.currencies   NOT NULL DEFAULT 'BRL',
            period      finance.budgetperiod NOT NULL DEFAULT 'monthly',
            is_active   BOOLEAN     NOT NULL DEFAULT true,
            created_at  TIMESTAMPTZ NOT NULL,
            updated_at  TIMESTAMPTZ NOT NULL,
            CONSTRAINT pk_budgets PRIMARY KEY (id),
            CONSTRAINT ck_budgets_family_or_category CHECK (
                (family_id IS NOT NULL OR category_id IS NOT NULL) AND
                NOT (family_id IS NOT NULL AND category_id IS NOT NULL)
            ),
            CONSTRAINT fk_budgets_user_id FOREIGN KEY (user_id) REFERENCES users(id),
            CONSTRAINT fk_budgets_family_id FOREIGN KEY (family_id)
                REFERENCES finance.tag_families(id) ON DELETE CASCADE,
            CONSTRAINT fk_budgets_category_id FOREIGN KEY (category_id)
                REFERENCES finance.categories(id) ON DELETE CASCADE
        )
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_budgets_user_id ON finance.budgets (user_id)
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_budgets_family_id ON finance.budgets (family_id)
    """))
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_budgets_category_id ON finance.budgets (category_id)
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP TABLE IF EXISTS finance.budgets"))
    conn.execute(sa.text("DROP TYPE IF EXISTS finance.budgetperiod"))
