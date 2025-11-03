"""add polymorphic type and tabular fields to data_set

Revision ID: 2460_polymorphic_single_table
Revises: 245ebd05958b
Create Date: 2025-11-02 21:00:00.000000
"""

import sqlalchemy as sa
from alembic import op

revision = "2460_polymorphic_single_table"
down_revision = "245ebd05958b"
branch_labels = None
depends_on = None


def upgrade():
    # Añade columna 'type' al modelo base
    op.add_column(
        "data_set",
        sa.Column("type", sa.String(length=50), nullable=False, server_default="uvl"),
    )
    op.create_index("ix_data_set_type", "data_set", ["type"])

    # Añade campos específicos para TabularDataset
    op.add_column("data_set", sa.Column("rows_count", sa.Integer(), nullable=True))
    op.add_column("data_set", sa.Column("schema_json", sa.Text(), nullable=True))

    # Actualiza registros existentes para marcar su tipo
    op.execute("UPDATE data_set SET type = 'uvl' WHERE type IS NULL")


def downgrade():
    op.drop_column("data_set", "schema_json")
    op.drop_column("data_set", "rows_count")
    op.drop_index("ix_data_set_type", table_name="data_set")
    op.drop_column("data_set", "type")
