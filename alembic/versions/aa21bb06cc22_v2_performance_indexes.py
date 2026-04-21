"""v2 performance indexes - BRIN and partial indexes for Supabase free tier

Revision ID: aa21bb06cc22
Revises: aa20bb05cc21
Create Date: 2026-04-20

Performance optimizations for Supabase free tier:
- BRIN indexes for time-series data (99% smaller than B-tree)
- Partial indexes for active records (exclude soft-deleted)
- Composite indexes for common query patterns
- Covering indexes to avoid table lookups
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa21bb06cc22"
down_revision: Union[str, None] = "aa20bb05cc21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # =========================================================================
    # BRIN INDEXES - For time-series data (much smaller than B-tree, good for ordered data)
    # =========================================================================
    
    # BRIN index for transactions by date - excellent for time-range queries
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_transactions_date_brin 
        ON finance.transactions USING BRIN (date_transaction)
        WITH (pages_per_range = 128)
    """))
    
    # BRIN index for net_worth_snapshots by date
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_net_worth_date_brin 
        ON finance.net_worth_snapshots USING BRIN (date)
        WITH (pages_per_range = 32)
    """))
    
    # =========================================================================
    # PARTIAL INDEXES - Only index active records, exclude soft-deleted
    # =========================================================================
    
    # Partial index for active transactions only (most common query)
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_transactions_active 
        ON finance.transactions (user_id, date_transaction DESC)
        WHERE created_at > (CURRENT_DATE - INTERVAL '2 years')
    """))
    
    # Partial index for active accounts
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_accounts_active 
        ON finance.accounts (user_id, name)
        WHERE is_active = true
    """))
    
    # Partial index for active credit cards
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_credit_cards_active 
        ON finance.credit_cards (user_id, payment_method_id)
        WHERE is_active = true
    """))
    
    # Partial index for open/closed invoices (not paid) - for faturas page
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_invoices_unpaid 
        ON finance.invoices (user_id, credit_card_id, due_date)
        WHERE status IN ('open', 'closed')
    """))
    
    # Partial index for active payment methods
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_payment_methods_active 
        ON finance.payment_methods (user_id, account_id, type)
        WHERE is_active = true
    """))
    
    # =========================================================================
    # COMPOSITE INDEXES - Covering indexes for common query patterns
    # =========================================================================
    
    # Covering index for transaction listing with all filters
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_transactions_listing 
        ON finance.transactions (user_id, date_transaction DESC, tag_id, account_id, invoice_id)
        INCLUDE (value, currency, description, created_at)
    """))
    
    # Index for net_worth latest snapshot lookup
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_net_worth_latest 
        ON finance.net_worth_snapshots (user_id, date DESC)
    """))
    
    # Index for budget queries by family
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_budgets_family_lookup 
        ON finance.budgets (user_id, family_id)
        WHERE is_active = true
    """))
    
    # Index for tag lookups with category
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_tags_category_lookup 
        ON finance.tags (category_id, user_id)
        WHERE is_active = true
    """))
    
    # Index for category lookups with family
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_categories_family_lookup 
        ON finance.categories (family_id, user_id)
    """))
    
    # Index for invoice aggregation queries
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_invoices_totals 
        ON finance.invoices (user_id, status, total_amount)
        WHERE status IN ('open', 'closed')
    """))
    
    # Index for transaction aggregations by tag (resumo page)
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_transactions_by_tag 
        ON finance.transactions (tag_id, user_id, date_transaction)
        INCLUDE (value)
    """))
    
    # Index for liability balance lookups
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_liabilities_balance 
        ON finance.liabilities (user_id, outstanding_balance)
        WHERE is_active = true
    """))


def downgrade() -> None:
    conn = op.get_bind()
    
    indexes = [
        "ix_finance_transactions_date_brin",
        "ix_finance_net_worth_date_brin",
        "ix_finance_transactions_active",
        "ix_finance_accounts_active",
        "ix_finance_credit_cards_active",
        "ix_finance_invoices_unpaid",
        "ix_finance_payment_methods_active",
        "ix_finance_transactions_listing",
        "ix_finance_net_worth_latest",
        "ix_finance_budgets_family_lookup",
        "ix_finance_tags_category_lookup",
        "ix_finance_categories_family_lookup",
        "ix_finance_invoices_totals",
        "ix_finance_transactions_by_tag",
        "ix_finance_liabilities_balance",
    ]
    
    for idx in indexes:
        conn.execute(sa.text(f"DROP INDEX IF EXISTS {idx}"))
