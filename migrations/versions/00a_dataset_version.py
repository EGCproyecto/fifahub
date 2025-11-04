"""dataset versioning

Revision ID: 00a_dataset_version
Revises: <PON_AQUI_TU_ULTIMA_REVISION>
Create Date: 2025-11-04 10:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "00a_dataset_version"
down_revision = "<ddba84b9a16a>"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dataset_version",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("data_set.id"), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("change_note", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dataset_version_dataset_id", "dataset_version", ["dataset_id"], unique=False)


def downgrade():
    op.drop_index("ix_dataset_version_dataset_id", table_name="dataset_version")
    op.drop_table("dataset_version")
