from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Importa tu app y db
from app import create_app, db

# Config Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Crea app y registra modelos en el metadata
app = create_app()
with app.app_context():
    # IMPORTA aquí todos los módulos que declaran modelos para que db.metadata los incluya
    try:
        from app.modules.auth import models as _auth_models  # noqa: F401
    except Exception:
        pass
    try:
        from app.modules.dataset import models as _dataset_models  # noqa: F401
    except Exception:
        pass
    try:
        # Si tienes modelos en otros módulos, impórtalos también
        from app.modules.tabular import models as _tabular_models  # noqa: F401
    except Exception:
        pass

    # (Opcional) Naming convention para constraints consistente entre entornos
    db.metadata.naming_convention = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    target_metadata = db.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = str(db.engine.url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = db.engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
