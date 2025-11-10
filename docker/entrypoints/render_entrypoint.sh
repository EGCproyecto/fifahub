mkdir -p docker/entrypoints
cat > docker/entrypoints/render_entrypoint.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail

export FLASK_APP=app:create_app

echo "⏳ Esperando a la base de datos..."
python3 - << 'PY'
import os, time, pymysql
host=os.environ['MARIADB_HOSTNAME']
port=int(os.environ.get('MARIADB_PORT', 3306))
user=os.environ['MARIADB_USER']
pw=os.environ['MARIADB_PASSWORD']
db=os.environ['MARIADB_DATABASE']
for i in range(60):
    try:
        pymysql.connect(host=host, port=port, user=user, password=pw, database=db, connect_timeout=5).close()
        print("✅ DB OK"); break
    except Exception as e:
        print(f"[{i:02d}] BD no disponible: {e}")
        time.sleep(2)
else:
    raise SystemExit("❌ Timeout esperando BD")
PY

echo "🔼 Ejecutando migraciones (upgrade real)..."
flask db upgrade

echo "🚀 Lanzando Gunicorn en $PORT"
exec gunicorn -w 2 -b 0.0.0.0:"$PORT" "app:create_app()"
SH
chmod +x docker/entrypoints/render_entrypoint.sh
