"""v2 drop payment_methods table

Revision ID: aa10bb09cc08
Revises: aa09bb10cc11
Create Date: 2026-04-18 00:10:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa10bb09cc08"
down_revision: Union[str, None] = "aa09bb10cc11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE finance.transactions t
        SET account_id = pm.account_id
        FROM finance.payment_methods pm
        WHERE t.payment_method_id = pm.id
        AND pm.account_id IS NOT NULL
        AND t.account_id IS NULL
    """))
    result = conn.execute(sa.text("""
        SELECT COUNT(*) FROM finance.transactions WHERE account_id IS NULL
    """))
    null_count = result.scalar()
    print(f"Transações com account_id NULL após migração de payment_methods: {null_count}")
    if null_count > 0:
        print("Atualizando account_id com primeira conta ativa de cada usuário...")
        conn.execute(sa.text("""
            UPDATE finance.transactions t
            SET account_id = a.id
            FROM finance.accounts a
            WHERE t.account_id IS NULL
            AND t.user_id = a.user_id
            AND a.is_active = true
        """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions
            DROP CONSTRAINT IF EXISTS fk_transactions_payment_method_id
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions
            DROP COLUMN IF EXISTS payment_method_id
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions
            ALTER COLUMN account_id SET NOT NULL
    """))
    conn.execute(sa.text("DROP TABLE IF EXISTS finance.payment_methods"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS finance.payment_methods (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            name VARCHAR NOT NULL,
            type VARCHAR NOT NULL,
            account_id UUID,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        )
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            ALTER TABLE finance.transactions
                ADD COLUMN IF NOT EXISTS payment_method_id UUID;
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.transactions
            ALTER COLUMN account_id DROP NOT NULL
    """))