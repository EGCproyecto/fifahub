#!/bin/bash

# ---------------------------------------------------------------------------
# Creative Commons CC BY 4.0 - David Romero - Diverso Lab
# ---------------------------------------------------------------------------
# This script is licensed under the Creative Commons Attribution 4.0 
# International License. You are free to share and adapt the material 
# as long as appropriate credit is given, a link to the license is provided, 
# and you indicate if changes were made.
#
# For more details, visit:
# https://creativecommons.org/licenses/by/4.0/
# ---------------------------------------------------------------------------

# Exit immediately if a command exits with a non-zero status
set -e

export FLASK_APP=app:create_app
export PORT="${PORT:-10000}"

# Wait for the database to be ready by running a script
sh ./scripts/wait-for-db.sh

# Check if the database is empty
TABLE_COUNT=$(mariadb -u $MARIADB_USER -p$MARIADB_PASSWORD -h $MARIADB_HOSTNAME -P $MARIADB_PORT -D $MARIADB_DATABASE -sse "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$MARIADB_DATABASE';")

if [ "$TABLE_COUNT" -eq 0 ]; then
 
    echo "Empty database, running all migrations..."
    flask db upgrade

    # Seed the database with initial data
    rosemary db:seed -y

else

    echo "Database already initialized, checking migrations..."

    # Get the current revision
    CURRENT_REVISION=$(mariadb -u $MARIADB_USER -p$MARIADB_PASSWORD -h $MARIADB_HOSTNAME -P $MARIADB_PORT -D $MARIADB_DATABASE -sse "SELECT version_num FROM alembic_version LIMIT 1;" 2>/dev/null || echo "")
    
    if [ -z "$CURRENT_REVISION" ]; then
        # Tables exist but no alembic version - stamp to base version, not head
        echo "WARNING: Tables exist but no alembic version. Stamping to base migration..."
        flask db stamp 2bbe9c8ccd1d
    fi

    # Apply pending migrations
    echo "Applying pending migrations..."
    flask db upgrade
fi

# Start the application using Gunicorn on the Render port
exec gunicorn --bind 0.0.0.0:$PORT app:app --log-level info --timeout 3600