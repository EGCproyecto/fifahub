"""create core tables (user, data_set, etc.)

Revision ID: 2bbe9c8ccd1d
Revises: 06516267ad45
Create Date: 2025-11-10 22:26:19.600634
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2bbe9c8ccd1d"
down_revision = "06516267ad45"
branch_labels = None
depends_on = None


def upgrade():
    # --- Tablas base sin dependencias o con dependencias claras ---
    op.create_table(
        "doi_mapping",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dataset_doi_old", sa.String(length=120), nullable=True),
        sa.Column("dataset_doi_new", sa.String(length=120), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "ds_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("number_of_models", sa.String(length=120), nullable=True),
        sa.Column("number_of_features", sa.String(length=120), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "fakenodo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meta_data", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=100), nullable=False),
        sa.Column("doi", sa.String(length=250), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doi"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "fm_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("solver", sa.Text(), nullable=True),
        sa.Column("not_solver", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=256), nullable=False),
        sa.Column("password", sa.String(length=256), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "zenodo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "ds_meta_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("deposition_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "publication_type",
            sa.Enum(
                "NONE",
                "ANNOTATION_COLLECTION",
                "BOOK",
                "BOOK_SECTION",
                "CONFERENCE_PAPER",
                "DATA_MANAGEMENT_PLAN",
                "JOURNAL_ARTICLE",
                "PATENT",
                "PREPRINT",
                "PROJECT_DELIVERABLE",
                "PROJECT_MILESTONE",
                "PROPOSAL",
                "REPORT",
                "SOFTWARE_DOCUMENTATION",
                "TAXONOMIC_TREATMENT",
                "TECHNICAL_NOTE",
                "THESIS",
                "WORKING_PAPER",
                "OTHER",
                name="publicationtype",
            ),
            nullable=False,
        ),
        sa.Column("publication_doi", sa.String(length=120), nullable=True),
        sa.Column("dataset_doi", sa.String(length=120), nullable=True),
        sa.Column("tags", sa.String(length=120), nullable=True),
        sa.Column("ds_metrics_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["ds_metrics_id"], ["ds_metrics.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "fm_meta_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uvl_filename", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "publication_type",
            sa.Enum(
                "NONE",
                "ANNOTATION_COLLECTION",
                "BOOK",
                "BOOK_SECTION",
                "CONFERENCE_PAPER",
                "DATA_MANAGEMENT_PLAN",
                "JOURNAL_ARTICLE",
                "PATENT",
                "PREPRINT",
                "PROJECT_DELIVERABLE",
                "PROJECT_MILESTONE",
                "PROPOSAL",
                "REPORT",
                "SOFTWARE_DOCUMENTATION",
                "TAXONOMIC_TREATMENT",
                "TECHNICAL_NOTE",
                "THESIS",
                "WORKING_PAPER",
                "OTHER",
                name="publicationtype",
            ),
            nullable=False,
        ),
        sa.Column("publication_doi", sa.String(length=120), nullable=True),
        sa.Column("tags", sa.String(length=120), nullable=True),
        sa.Column("uvl_version", sa.String(length=120), nullable=True),
        sa.Column("fm_metrics_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["fm_metrics_id"], ["fm_metrics.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "notepad",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "user_profile",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("orcid", sa.String(length=19), nullable=True),
        sa.Column("affiliation", sa.String(length=100), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("surname", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "author",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("affiliation", sa.String(length=120), nullable=True),
        sa.Column("orcid", sa.String(length=120), nullable=True),
        sa.Column("ds_meta_data_id", sa.Integer(), nullable=True),
        sa.Column("fm_meta_data_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["ds_meta_data_id"], ["ds_meta_data.id"]),
        sa.ForeignKeyConstraint(["fm_meta_data_id"], ["fm_meta_data.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "data_set",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("ds_meta_data_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("type", sa.String(length=50), server_default="uvl", nullable=False),
        sa.Column("rows_count", sa.Integer(), nullable=True),
        sa.Column("schema_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["ds_meta_data_id"], ["ds_meta_data.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_index(op.f("ix_data_set_type"), "data_set", ["type"], unique=False)

    # --- dataset_version: AHORA se crea explícitamente y con FKs con nombre ---
    op.create_table(
        "dataset_version",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("change_note", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["author_id"], ["user.id"], name="fk_dataset_version_author"),
        sa.ForeignKeyConstraint(["dataset_id"], ["data_set.id"], name="fk_dataset_version_data_set"),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "ds_download_record",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("dataset_id", sa.Integer(), nullable=True),
        sa.Column("download_date", sa.DateTime(), nullable=False),
        sa.Column("download_cookie", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["data_set.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "ds_view_record",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("dataset_id", sa.Integer(), nullable=True),
        sa.Column("view_date", sa.DateTime(), nullable=False),
        sa.Column("view_cookie", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["data_set.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "feature_model",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("data_set_id", sa.Integer(), nullable=False),
        sa.Column("fm_meta_data_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["data_set_id"], ["data_set.id"]),
        sa.ForeignKeyConstraint(["fm_meta_data_id"], ["fm_meta_data.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "tabular_meta_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hubfile_id", sa.Integer(), nullable=True),
        sa.Column("delimiter", sa.String(length=5), nullable=True),
        sa.Column("encoding", sa.String(length=20), nullable=True),
        sa.Column("has_header", sa.Boolean(), nullable=True),
        sa.Column("n_rows", sa.Integer(), nullable=True),
        sa.Column("n_cols", sa.Integer(), nullable=True),
        sa.Column("primary_keys", sa.JSON(), nullable=True),
        sa.Column("index_cols", sa.JSON(), nullable=True),
        sa.Column("sample_rows", sa.JSON(), nullable=True),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["data_set.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "tabular_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("null_ratio", sa.Float(), nullable=True),
        sa.Column("avg_cardinality", sa.Float(), nullable=True),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["data_set.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "file",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("checksum", sa.String(length=120), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("feature_model_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["feature_model_id"], ["feature_model.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "tabular_column",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("dtype", sa.String(length=50), nullable=True),
        sa.Column("null_count", sa.Integer(), nullable=True),
        sa.Column("unique_count", sa.Integer(), nullable=True),
        sa.Column("stats", sa.JSON(), nullable=True),
        sa.Column("meta_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["meta_id"], ["tabular_meta_data.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "file_download_record",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("file_id", sa.Integer(), nullable=True),
        sa.Column("download_date", sa.DateTime(), nullable=False),
        sa.Column("download_cookie", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["file.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "file_view_record",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("view_date", sa.DateTime(), nullable=True),
        sa.Column("view_cookie", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["file_id"], ["file.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    # IMPORTANTE: Se han ELIMINADO estas líneas que te rompían:
    # op.create_foreign_key(None, "dataset_version", "data_set", ["dataset_id"], ["id"])
    # op.create_foreign_key(None, "dataset_version", "user", ["author_id"], ["id"])


def downgrade():
    # Bajar primero lo que depende de otras tablas
    op.drop_table("file_view_record")
    op.drop_table("file_download_record")
    op.drop_table("tabular_column")
    op.drop_table("file")
    op.drop_table("tabular_metrics")
    op.drop_table("tabular_meta_data")
    op.drop_table("feature_model")
    op.drop_table("ds_view_record")
    op.drop_table("ds_download_record")

    # Caer la tabla que referencia a data_set/user ANTES de data_set/user
    op.drop_table("dataset_version")

    op.drop_index(op.f("ix_data_set_type"), table_name="data_set")
    op.drop_table("data_set")
    op.drop_table("author")
    op.drop_table("user_profile")
    op.drop_table("notepad")
    op.drop_table("fm_meta_data")
    op.drop_table("ds_meta_data")
    op.drop_table("zenodo")
    op.drop_table("user")
    op.drop_table("fm_metrics")
    op.drop_table("fakenodo")
    op.drop_table("ds_metrics")
    op.drop_table("doi_mapping")
