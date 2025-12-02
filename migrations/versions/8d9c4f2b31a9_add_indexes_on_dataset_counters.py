"""add indexes on dataset counters

Revision ID: 8d9c4f2b31a9
Revises: 4f0f9c3c0d1a
Create Date: 2025-12-02 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8d9c4f2b31a9"
down_revision = "4f0f9c3c0d1a"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "data_set",
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        op.f("ix_data_set_view_count"),
        "data_set",
        ["view_count"],
        unique=False,
    )
    op.create_index(
        op.f("ix_data_set_download_count"),
        "data_set",
        ["download_count"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_data_set_download_count"), table_name="data_set")
    op.drop_index(op.f("ix_data_set_view_count"), table_name="data_set")
    op.drop_column("data_set", "view_count")
