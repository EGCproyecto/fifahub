"""Initial migration after reset

Revision ID: 06516267ad45
Revises:
Create Date: 2025-11-09 21:37:24.785414
"""

import sqlalchemy as sa
from alembic import op

revision = "06516267ad45"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Tabla dependiente SIN FKs para evitar errno 150 en BD vacía
    op.create_table(
        "dataset_version",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),  # SET NULL => nullable=True
        sa.Column("change_note", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    with op.batch_alter_table("dataset_version") as batch_op:
        batch_op.create_index(
            batch_op.f("ix_dataset_version_dataset_id"),
            ["dataset_id"],
            unique=False,
        )

    # Añadir FKs de forma defensiva si las tablas referenciadas existen
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_tables = set(insp.get_table_names())

    def _has_col(table, col):
        try:
            return any(c["name"] == col for c in insp.get_columns(table))
        except Exception:
            return False

    if "user" in existing_tables and _has_col("user", "id"):
        try:
            op.create_foreign_key(
                "fk_dataset_version_author",
                "dataset_version",
                "user",
                ["author_id"],
                ["id"],
                ondelete="SET NULL",
            )
        except Exception:
            pass

    if "data_set" in existing_tables and _has_col("data_set", "id"):
        try:
            op.create_foreign_key(
                "fk_dataset_version_dataset",
                "dataset_version",
                "data_set",
                ["dataset_id"],
                ["id"],
                ondelete="CASCADE",
            )
        except Exception:
            pass


def downgrade():
    with op.batch_alter_table("dataset_version") as batch_op:
        try:
            batch_op.drop_constraint("fk_dataset_version_author", type_="foreignkey")
        except Exception:
            pass
        try:
            batch_op.drop_constraint("fk_dataset_version_dataset", type_="foreignkey")
        except Exception:
            pass
        batch_op.drop_index(batch_op.f("ix_dataset_version_dataset_id"))

    op.drop_table("dataset_version")
