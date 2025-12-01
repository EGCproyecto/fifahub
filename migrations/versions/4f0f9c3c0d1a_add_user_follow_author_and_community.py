"""add user follow author and community tables

Revision ID: 4f0f9c3c0d1a
Revises: b5d4a1f22a57
Create Date: 2025-02-14 02:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "4f0f9c3c0d1a"
down_revision = "b5d4a1f22a57"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_follow_author",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["author.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id",
            "author_id",
            name="uq_user_follow_author_user_author",
        ),
    )
    op.create_index(
        "ix_user_follow_author_user_id",
        "user_follow_author",
        ["user_id"],
    )
    op.create_index(
        "ix_user_follow_author_author_id",
        "user_follow_author",
        ["author_id"],
    )

    op.create_table(
        "user_follow_community",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("community_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "user_id",
            "community_id",
            name="uq_user_follow_community_user_community",
        ),
    )
    op.create_index(
        "ix_user_follow_community_user_id",
        "user_follow_community",
        ["user_id"],
    )
    op.create_index(
        "ix_user_follow_community_community_id",
        "user_follow_community",
        ["community_id"],
    )


def downgrade():
    op.drop_index("ix_user_follow_community_community_id", table_name="user_follow_community")
    op.drop_index("ix_user_follow_community_user_id", table_name="user_follow_community")
    op.drop_table("user_follow_community")

    op.drop_index("ix_user_follow_author_author_id", table_name="user_follow_author")
    op.drop_index("ix_user_follow_author_user_id", table_name="user_follow_author")
    op.drop_table("user_follow_author")
