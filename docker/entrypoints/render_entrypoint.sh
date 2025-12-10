#!/bin/bash
set -euo pipefail

export FLASK_APP=app:create_app
export PORT="${PORT:-10000}"

echo "Waiting for database..."
sh ./scripts/wait-for-db.sh

export MYSQL_PWD="$MARIADB_PASSWORD"

echo "Checking database state..."
TABLE_COUNT=$(mariadb -u "$MARIADB_USER" -h "$MARIADB_HOSTNAME" -P "$MARIADB_PORT" -D "$MARIADB_DATABASE" -sse \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$MARIADB_DATABASE';" 2>/dev/null || echo "0")

if [ "$TABLE_COUNT" -eq 0 ]; then
    echo "Empty database detected"
    unset MYSQL_PWD
    
    if [ ! -d "migrations/versions" ]; then
        flask db init
        flask db migrate -m "initial"
    fi
    
    flask db upgrade
    
    if command -v rosemary >/dev/null 2>&1; then
        rosemary db:seed -y
    fi
else
    echo "Existing database detected"
    
    ALEMBIC_EXISTS=$(mariadb -u "$MARIADB_USER" -h "$MARIADB_HOSTNAME" -P "$MARIADB_PORT" -D "$MARIADB_DATABASE" -sse \
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '$MARIADB_DATABASE' AND table_name = 'alembic_version';" 2>/dev/null || echo "0")
    
    if [ "$ALEMBIC_EXISTS" -eq 0 ]; then
        echo "No alembic_version table, creating..."
        unset MYSQL_PWD
        flask db stamp head
        flask db upgrade
    else
        CURRENT_VERSION=$(mariadb -u "$MARIADB_USER" -h "$MARIADB_HOSTNAME" -P "$MARIADB_PORT" -D "$MARIADB_DATABASE" -sse \
            "SELECT version_num FROM alembic_version LIMIT 1;" 2>/dev/null || echo "")
        
        if [ -z "$CURRENT_VERSION" ]; then
            echo "Empty alembic_version, stamping..."
            unset MYSQL_PWD
            flask db stamp head
            echo "Applying missing migrations..."
            flask db upgrade
        else
            echo "Current version: $CURRENT_VERSION"
            
            VALID_VERSIONS="06516267ad45 2bbe9c8ccd1d 229dfdde23b3 b5d4a1f22a57 4f0f9c3c0d1a 8d9c4f2b31a9"
            
            if ! echo "$VALID_VERSIONS" | grep -qw "$CURRENT_VERSION"; then
                echo "Ghost version detected: $CURRENT_VERSION"
                mariadb -u "$MARIADB_USER" -h "$MARIADB_HOSTNAME" -P "$MARIADB_PORT" -D "$MARIADB_DATABASE" -e \
                    "DELETE FROM alembic_version WHERE version_num = '$CURRENT_VERSION';"
                unset MYSQL_PWD
                echo "Repairing with stamp head..."
                flask db stamp head
                echo "Applying missing migrations..."
                flask db upgrade
            else
                unset MYSQL_PWD
            fi
        fi
        
        echo "Applying migrations..."
        if ! flask db upgrade 2>&1; then
            echo "Upgrade failed, attempting repair..."
            
            export MYSQL_PWD="$MARIADB_PASSWORD"
            mariadb -u "$MARIADB_USER" -h "$MARIADB_HOSTNAME" -P "$MARIADB_PORT" -D "$MARIADB_DATABASE" -e \
                "DROP TABLE IF EXISTS alembic_version;"
            unset MYSQL_PWD
            
            flask db stamp head
            flask db upgrade
        fi
    fi
fi

unset MYSQL_PWD 2>/dev/null || true

echo "Starting Gunicorn on port $PORT"
exec gunicorn -w "${WEB_CONCURRENCY:-2}" -b "0.0.0.0:$PORT" app:app --log-level info --timeout 3600