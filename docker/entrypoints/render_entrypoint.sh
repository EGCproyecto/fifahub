#!/usr/bin/env bash
set -euo pipefail

# ===== Config básica =====
export FLASK_APP=app:create_app
export PORT="${PORT:-10000}"     # Render inyecta $PORT; si no, 10000
export MIGRATIONS_ONLY=1         # Evita cargar módulos pesados (flamapy/ANTLR) durante migraciones

echo "⏳ Esperando a la base de datos..."
python3 - << 'PY'
import os, time, pymysql, sys
host=os.environ['MARIADB_HOSTNAME']
port=int(os.environ.get('MARIADB_PORT', 3306))
user=os.environ['MARIADB_USER']
pw=os.environ['MARIADB_PASSWORD']
db=os.environ['MARIADB_DATABASE']

for i in range(90):
    try:
        conn=pymysql.connect(host=host, port=port, user=user, password=pw, database=db, connect_timeout=5)
        with conn.cursor() as c: c.execute("SELECT 1")
        conn.close()
        print("✅ DB OK")
        sys.exit(0)
    except Exception as e:
        print(f"[{i:02d}] BD no disponible: {e}")
        time.sleep(2)
print("❌ Timeout esperando BD"); sys.exit(1)
PY

echo "🔧 Comprobando estado de Alembic..."
python3 - << 'PY'
import os, pymysql, json
host=os.environ['MARIADB_HOSTNAME']
port=int(os.environ.get('MARIADB_PORT', 3306))
user=os.environ['MARIADB_USER']
pw=os.environ['MARIADB_PASSWORD']
db=os.environ['MARIADB_DATABASE']

state = {"has_alembic": False, "alembic_version": None, "has_tables": False}
conn = pymysql.connect(host=host, port=port, user=user, password=pw, database=db)
try:
    with conn.cursor() as c:
        c.execute("SHOW TABLES")
        tables = [row[0] for row in c.fetchall()]
        state["has_tables"] = len(tables) > 0
        if "alembic_version" in tables:
            state["has_alembic"] = True
            c.execute("SELECT version_num FROM alembic_version LIMIT 1")
            row = c.fetchone()
            state["alembic_version"] = row[0] if row else None
finally:
    conn.close()
print(json.dumps(state))
PY

echo "🔼 Ejecutando migraciones (flask db upgrade)..."
# Primer intento "normal"
if ! flask db upgrade; then
  echo "⚠️  Upgrade falló. Intento de 'stamp head' y reintento (para esquemas ya creados)."
  flask db stamp head || true
  flask db upgrade
fi

# (Opcional) seed solo si la BD estaba vacía antes del upgrade
if command -v rosemary >/dev/null 2>&1; then
  echo "🌱 Seed (solo si procede)..."
  # no fallar si no hay comando/seed
  rosemary db:seed -y || true
fi

# A partir de aquí ya puede cargar flamapy/ANTLR con normalidad
unset MIGRATIONS_ONLY

echo "🚀 Lanzando Gunicorn en $PORT"
exec gunicorn -w "${WEB_CONCURRENCY:-2}" -b "0.0.0.0:${PORT}" "app:create_app()"
