import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "06516267ad45"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dataset_version",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("change_note", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        mysql_engine="InnoDB",
        mysql_default_charset="utf8mb4",
    )
    # NO foreign keys aquí. Se añaden en la siguiente migración.


def downgrade():
    op.drop_table("dataset_version")
