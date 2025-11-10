#!/usr/bin/env sh
set -eu

# Asegura FLASK_APP
export FLASK_APP="app:create_app"

echo "⏳ Esperando a la base de datos..."
python - <<'PY'
import os, time, sys
try:
    import pymysql
except Exception as e:
    print("❌ Falta pymysql. Añádelo a requirements.txt", e, file=sys.stderr)
    sys.exit(1)

host = os.environ.get('MARIADB_HOSTNAME')
port = int(os.environ.get('MARIADB_PORT', '3306'))
user = os.environ.get('MARIADB_USER')
pwd  = os.environ.get('MARIADB_PASSWORD')
db   = os.environ.get('MARIADB_DATABASE')

for i in range(60):
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=pwd, database=db, connect_timeout=3)
        conn.close()
        print("✅ DB OK")
        break
    except Exception as e:
        print(f"[{i:02d}] BD no disponible: {e}")
        time.sleep(2)
else:
    print("❌ Timeout esperando BD", file=sys.stderr)
    sys.exit(1)
PY

echo "🔼 Ejecutando migraciones (flask db upgrade)..."
flask db upgrade

PORT="${PORT:-5000}"
echo "🚀 Lanzando Gunicorn en 0.0.0.0:${PORT}"
exec gunicorn --bind "0.0.0.0:${PORT}" "app:create_app()" --log-level info --timeout 3600 --workers 2
