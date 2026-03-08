"""cascade deletes and unique family name

Revision ID: d2e3f4a5b6c1
Revises: c1d2e3f4a5b6
Create Date: 2026-03-08 04:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d2e3f4a5b6c1"
down_revision: Union[str, None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _constraint_exists(conn, table: str, constraint_name: str, schema: str = "finance") -> bool:
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.table_constraints "
            "WHERE table_schema = :schema AND table_name = :table AND constraint_name = :name"
        ),
        {"schema": schema, "table": table, "name": constraint_name},
    )
    return result.first() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Unique constraint on tag_families(user_id, name)
    if not _constraint_exists(conn, "tag_families", "uq_tag_families_user_name"):
        op.create_unique_constraint(
            "uq_tag_families_user_name",
            "tag_families",
            ["user_id", "name"],
            schema="finance",
        )

    # 2. categories.family_id: SET NULL → CASCADE
    # Drop existing FK (find its name first)
    result = conn.execute(
        sa.text(
            "SELECT constraint_name FROM information_schema.table_constraints "
            "WHERE table_schema = 'finance' AND table_name = 'categories' "
            "AND constraint_type = 'FOREIGN KEY'"
        )
    )
    for row in result:
        cname = row[0]
        # Only drop the FK that references tag_families
        check = conn.execute(
            sa.text(
                "SELECT 1 FROM information_schema.referential_constraints rc "
                "JOIN information_schema.table_constraints tc "
                "ON rc.unique_constraint_name = tc.constraint_name "
                "WHERE rc.constraint_name = :name "
                "AND tc.table_name = 'tag_families'"
            ),
            {"name": cname},
        )
        if check.first():
            op.drop_constraint(cname, "categories", schema="finance", type_="foreignkey")

    op.create_foreign_key(
        "fk_categories_family_id",
        "categories",
        "tag_families",
        ["family_id"],
        ["id"],
        source_schema="finance",
        referent_schema="finance",
        ondelete="CASCADE",
    )

    # 3. tags.category_id: RESTRICT → CASCADE
    result = conn.execute(
        sa.text(
            "SELECT constraint_name FROM information_schema.table_constraints "
            "WHERE table_schema = 'finance' AND table_name = 'tags' "
            "AND constraint_type = 'FOREIGN KEY'"
        )
    )
    for row in result:
        cname = row[0]
        check = conn.execute(
            sa.text(
                "SELECT 1 FROM information_schema.referential_constraints rc "
                "JOIN information_schema.table_constraints tc "
                "ON rc.unique_constraint_name = tc.constraint_name "
                "WHERE rc.constraint_name = :name "
                "AND tc.table_name = 'categories'"
            ),
            {"name": cname},
        )
        if check.first():
            op.drop_constraint(cname, "tags", schema="finance", type_="foreignkey")

    op.create_foreign_key(
        "fk_tags_category_id",
        "tags",
        "categories",
        ["category_id"],
        ["id"],
        source_schema="finance",
        referent_schema="finance",
        ondelete="CASCADE",
    )

    # 4. transactions.tag_id: RESTRICT → CASCADE
    result = conn.execute(
        sa.text(
            "SELECT constraint_name FROM information_schema.table_constraints "
            "WHERE table_schema = 'finance' AND table_name = 'transactions' "
            "AND constraint_type = 'FOREIGN KEY'"
        )
    )
    for row in result:
        cname = row[0]
        check = conn.execute(
            sa.text(
                "SELECT 1 FROM information_schema.referential_constraints rc "
                "JOIN information_schema.table_constraints tc "
                "ON rc.unique_constraint_name = tc.constraint_name "
                "WHERE rc.constraint_name = :name "
                "AND tc.table_name = 'tags'"
            ),
            {"name": cname},
        )
        if check.first():
            op.drop_constraint(cname, "transactions", schema="finance", type_="foreignkey")

    op.create_foreign_key(
        "fk_transactions_tag_id",
        "transactions",
        "tags",
        ["tag_id"],
        ["id"],
        source_schema="finance",
        referent_schema="finance",
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # Revert cascade → restrict / set null
    op.drop_constraint("fk_transactions_tag_id", "transactions", schema="finance", type_="foreignkey")
    op.create_foreign_key(
        None, "transactions", "tags", ["tag_id"], ["id"],
        source_schema="finance", referent_schema="finance",
    )

    op.drop_constraint("fk_tags_category_id", "tags", schema="finance", type_="foreignkey")
    op.create_foreign_key(
        None, "tags", "categories", ["category_id"], ["id"],
        source_schema="finance", referent_schema="finance",
    )

    op.drop_constraint("fk_categories_family_id", "categories", schema="finance", type_="foreignkey")
    op.create_foreign_key(
        None, "categories", "tag_families", ["family_id"], ["id"],
        source_schema="finance", referent_schema="finance",
        ondelete="SET NULL",
    )

    op.drop_constraint("uq_tag_families_user_name", "tag_families", schema="finance", type_="unique")
