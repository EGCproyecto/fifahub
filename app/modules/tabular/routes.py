# app/modules/tabular/routes.py

# 1. IMPORTA el blueprint "jefe" desde el __init__.py
from . import tabular_bp


# 2. AÑADE rutas
@tabular_bp.route("/upload")
def upload_tabular():
    return "Aquí irá la subida de CSVs de FIFA"
