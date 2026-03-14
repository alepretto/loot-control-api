"""create agent schema with messages and memories tables

Revision ID: f4a5b6c1d2e3
Revises: e3f4a5b6c1d2
Create Date: 2026-03-14 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f4a5b6c1d2e3"
down_revision: Union[str, None] = "e3f4a5b6c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, table: str, schema: str) -> bool:
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = :schema AND table_name = :table"
        ),
        {"schema": schema, "table": table},
    )
    return result.first() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Create schema agent if not exists
    conn.execute(sa.text("CREATE SCHEMA IF NOT EXISTS agent"))

    # 2. Create agent.messages
    if not _table_exists(conn, "messages", "agent"):
        op.create_table(
            "messages",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            schema="agent",
        )
        op.create_index(
            "ix_agent_messages_user_id",
            "messages",
            ["user_id"],
            schema="agent",
        )

    # 3. Create agent.memories
    if not _table_exists(conn, "memories", "agent"):
        op.create_table(
            "memories",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("user_id", sa.UUID(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
            schema="agent",
        )
        op.create_index(
            "ix_agent_memories_user_id",
            "memories",
            ["user_id"],
            schema="agent",
        )


def downgrade() -> None:
    conn = op.get_bind()

    if _table_exists(conn, "memories", "agent"):
        op.drop_index("ix_agent_memories_user_id", table_name="memories", schema="agent")
        op.drop_table("memories", schema="agent")

    if _table_exists(conn, "messages", "agent"):
        op.drop_index("ix_agent_messages_user_id", table_name="messages", schema="agent")
        op.drop_table("messages", schema="agent")

    conn.execute(sa.text("DROP SCHEMA IF EXISTS agent"))
