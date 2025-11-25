"""add download count to dataset

Revision ID: 229dfdde23b3
Revises: 2bbe9c8ccd1d
Create Date: 2025-11-12 16:05:50.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "229dfdde23b3"
down_revision = "2bbe9c8ccd1d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "data_set",
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("data_set", "download_count")
