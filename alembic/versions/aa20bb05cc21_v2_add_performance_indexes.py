"""v2 add performance indexes for Supabase free tier

Revision ID: aa20bb05cc21
Revises: aa19bb04cc20
Create Date: 2026-04-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa20bb05cc21"
down_revision: Union[str, None] = "aa19bb04cc20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Índice para joins com Tag (category_id, family_id filters)
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_transactions_tag_id 
        ON finance.transactions (tag_id)
    """))
    
    # Índice composto otimizado para queries de listagem com ordenação
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_transactions_user_date_desc 
        ON finance.transactions (user_id, date_transaction DESC)
    """))
    
    # Índice para filtros por conta + data (dashboard queries)
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_transactions_account_date 
        ON finance.transactions (account_id, date_transaction DESC)
    """))
    
    # Índice para faturas por cartão + status (queries rápidas de faturas)
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_invoices_card_status 
        ON finance.invoices (credit_card_id, status)
    """))
    
    # Índice para tags por categoria (joins frequentes)
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_tags_category_id 
        ON finance.tags (category_id)
    """))
    
    # Índice para categorias por família
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_categories_family_id 
        ON finance.categories (family_id)
    """))
    
    # Índice parcial para transações do mês atual (consultas de dashboard)
    conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS ix_finance_transactions_current_month 
        ON finance.transactions (user_id, date_transaction DESC)
        WHERE date_transaction >= date_trunc('month', CURRENT_DATE)
    """))


def downgrade() -> None:
    conn = op.get_bind()
    
    conn.execute(sa.text("""
        DROP INDEX IF EXISTS ix_finance_transactions_tag_id
    """))
    conn.execute(sa.text("""
        DROP INDEX IF EXISTS ix_finance_transactions_user_date_desc
    """))
    conn.execute(sa.text("""
        DROP INDEX IF EXISTS ix_finance_transactions_account_date
    """))
    conn.execute(sa.text("""
        DROP INDEX IF EXISTS ix_finance_invoices_card_status
    """))
    conn.execute(sa.text("""
        DROP INDEX IF EXISTS ix_finance_tags_category_id
    """))
    conn.execute(sa.text("""
        DROP INDEX IF EXISTS ix_finance_categories_family_id
    """))
    conn.execute(sa.text("""
        DROP INDEX IF EXISTS ix_finance_transactions_current_month
    """))
