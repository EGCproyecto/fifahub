#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

-
export FLASK_APP=app:create_app

# Wait for the database to be ready
sh ./scripts/wait-for-db.sh

# Initialize migrations only if the migrations directory doesn't exist
if [ ! -d "migrations/versions" ]; then
    flask db init
    flask db migrate
fi

# Check if the database is empty 
if [ $(mariadb -u $MARIADB_USER -p$MARIADB_PASSWORD -h $MARIADB_HOSTNAME -P $MARIADB_PORT -D $MARIADB_DATABASE -sse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$MARIADB_DATABASE';") -eq 0 ]; then
 
    echo "Empty database, migrating..."
    flask db upgrade
    
    rosemary db:seed -y

else

    echo "Database already initialized, checking migrations..."

    # Check specifically if alembic_version table exists to avoid crash
    TABLE_EXISTS=$(mariadb -u $MARIADB_USER -p$MARIADB_PASSWORD -h $MARIADB_HOSTNAME -P $MARIADB_PORT -D $MARIADB_DATABASE -sse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$MARIADB_DATABASE' AND table_name = 'alembic_version';")

    if [ "$TABLE_EXISTS" -eq 0 ]; then
        echo "⚠️  Tabla alembic_version perdida. Restaurando historial..."
        flask db stamp head
    fi

    # Apply upgrades
    flask db upgrade
fi


echo "🚀 Arrancando en el puerto $PORT..."
exec gunicorn --bind 0.0.0.0:$PORT app:app --log-level info --timeout 3600