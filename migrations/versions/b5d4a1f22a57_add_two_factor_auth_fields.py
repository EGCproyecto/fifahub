import sqlalchemy as sa
from alembic import op

revision = "b5d4a1f22a57"
down_revision = "229dfdde23b3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column("two_factor_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "user",
        sa.Column("two_factor_secret", sa.String(length=512), nullable=True),
    )
    op.create_table(
        "user_two_factor_recovery_code",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("encrypted_code", sa.String(length=512), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_two_factor_recovery_code_user_id",
        "user_two_factor_recovery_code",
        ["user_id"],
    )
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.alter_column(
            "user",
            "two_factor_enabled",
            server_default=None,
            existing_type=sa.Boolean(),
        )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.alter_column(
            "user",
            "two_factor_enabled",
            server_default=sa.text("0"),
            existing_type=sa.Boolean(),
        )
    op.drop_index("ix_user_two_factor_recovery_code_user_id", table_name="user_two_factor_recovery_code")
    op.drop_table("user_two_factor_recovery_code")
    op.drop_column("user", "two_factor_secret")
    op.drop_column("user", "two_factor_enabled")
