"""v2 refactor tag_families (add nature, is_active) and tags (remove type, add income_type)

Revision ID: aa03bb04cc05
Revises: aa02bb03cc04
Create Date: 2026-04-18 00:03:00.000000

NOTA: tag_families.nature é nullable — famílias existentes precisam ser
classificadas pelo usuário via tela de migração guiada pós-deploy.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "aa03bb04cc05"
down_revision: Union[str, None] = "aa02bb03cc04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # tag_families
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE finance.familynature AS ENUM
                ('fixed_expense','variable_expense','income','investment');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.tag_families
            ADD COLUMN IF NOT EXISTS nature finance.familynature
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.tag_families
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true
    """))

    # tags
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE finance.incometype AS ENUM ('active','passive','sporadic');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.tags
            ADD COLUMN IF NOT EXISTS income_type finance.incometype
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.tags DROP COLUMN IF EXISTS type
    """))
    conn.execute(sa.text("DROP TYPE IF EXISTS finance.categorytype"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE finance.categorytype AS ENUM ('outcome','income');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.tags
            ADD COLUMN IF NOT EXISTS type finance.categorytype
    """))
    conn.execute(sa.text("""
        UPDATE finance.tags SET type = 'outcome'::finance.categorytype WHERE type IS NULL
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.tags ALTER COLUMN type SET NOT NULL
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.tags DROP COLUMN IF EXISTS income_type
    """))
    conn.execute(sa.text("DROP TYPE IF EXISTS finance.incometype"))
    conn.execute(sa.text("""
        ALTER TABLE finance.tag_families DROP COLUMN IF EXISTS is_active
    """))
    conn.execute(sa.text("""
        ALTER TABLE finance.tag_families DROP COLUMN IF EXISTS nature
    """))
    conn.execute(sa.text("DROP TYPE IF EXISTS finance.familynature"))
