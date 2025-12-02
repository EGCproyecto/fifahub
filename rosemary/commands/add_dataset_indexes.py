import click
import sqlalchemy as sa
from flask.cli import with_appcontext
from sqlalchemy import inspect

from app import db


@click.command(
    "db:add-dataset-indexes",
    help="Ensure data_set has view/download count columns and indexes for fast sorting.",
)
@with_appcontext
def add_dataset_indexes():
    engine = db.engine
    inspector = inspect(engine)

    if "data_set" not in inspector.get_table_names():
        click.echo(click.style("Table 'data_set' does not exist. Run migrations first.", fg="red"))
        return

    columns = {col["name"] for col in inspector.get_columns("data_set")}
    statements = []

    if "view_count" not in columns:
        statements.append(sa.text("ALTER TABLE data_set ADD COLUMN view_count INT NOT NULL DEFAULT 0"))
    if "download_count" not in columns:
        statements.append(sa.text("ALTER TABLE data_set ADD COLUMN download_count INT NOT NULL DEFAULT 0"))

    if statements:
        with engine.begin() as conn:
            for stmt in statements:
                conn.execute(stmt)
        click.echo(click.style("Added missing counter columns to data_set.", fg="yellow"))

    # Refresh inspector after possible column changes
    inspector = inspect(engine)
    existing_indexes = {ix["name"] for ix in inspector.get_indexes("data_set")}
    index_statements = []

    if "ix_data_set_view_count" not in existing_indexes and "view_count" in {
        col["name"] for col in inspector.get_columns("data_set")
    }:
        index_statements.append(sa.text("CREATE INDEX ix_data_set_view_count ON data_set (view_count)"))

    if "ix_data_set_download_count" not in existing_indexes and "download_count" in {
        col["name"] for col in inspector.get_columns("data_set")
    }:
        index_statements.append(sa.text("CREATE INDEX ix_data_set_download_count ON data_set (download_count)"))

    if index_statements:
        with engine.begin() as conn:
            for stmt in index_statements:
                conn.execute(stmt)
        click.echo(click.style("Created missing indexes for counter columns.", fg="green"))
    else:
        click.echo(click.style("Counter indexes already present.", fg="blue"))
