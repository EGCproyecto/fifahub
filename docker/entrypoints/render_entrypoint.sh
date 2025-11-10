#!/usr/bin/env bash
set -euo pipefail

# Asegura factory app
export FLASK_APP=app:create_app

echo "⏳ Esperando a la base de datos..."
python3 - << 'PY'
import os, time, pymysql
host = os.environ['MARIADB_HOSTNAME']
port = int(os.environ.get('MARIADB_PORT', 3306))
user = os.environ['MARIADB_USER']
password = os.environ['MARIADB_PASSWORD']
db = os.environ['MARIADB_DATABASE']

for i in range(60):
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password, database=db, connect_timeout=5)
        conn.close()
        print("✅ DB OK")
        break
    except Exception as e:
        print(f"DB no disponible aún: {e}")
        time.sleep(2)
else:
    raise SystemExit("❌ Timeout esperando DB")
PY

# (Opcional) Solo si no existe estructura de migraciones en el contenedor (caso raro)
if [ ! -d "migrations" ] || [ ! -d "migrations/versions" ]; then
  echo "🧩 Inicializando migraciones (caso excepcional)..."
  flask db init
  # ATENCIÓN: 'migrate' en servidor solo si sabes que env.py carga TODOS los modelos
  flask db migrate -m "Baseline autogenerada en servidor"
fi

echo "🔼 Ejecutando migraciones (upgrade real)..."
flask db upgrade

# (Opcional) Seed si la BD está vacía de tus datos de negocio
# pip install -e ./    # si necesitas rosemary instalado en runtime
# rosemary db:seed -y  # si el seed es idempotente

echo "🚀 Lanzando Gunicorn en \$PORT"
exec gunicorn -w 2 -b 0.0.0.0:"$PORT" "app:create_app()"
