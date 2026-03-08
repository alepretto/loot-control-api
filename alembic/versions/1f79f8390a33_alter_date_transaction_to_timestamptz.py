"""alter date_transaction to timestamptz

Revision ID: 1f79f8390a33
Revises: cfa05bb32377
Create Date: 2026-03-08 01:29:46.892262

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = '1f79f8390a33'
down_revision: Union[str, None] = 'cfa05bb32377'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'transactions',
        'date_transaction',
        existing_type=sa.DateTime(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        schema='finance',
    )


def downgrade() -> None:
    op.alter_column(
        'transactions',
        'date_transaction',
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
        schema='finance',
    )
