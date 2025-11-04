# app/modules/tabular/__init__.py
"""Módulo Tabular: lógica y vistas para datasets CSV."""

from flask import Blueprint

# 1. DEFINE el blueprint
tabular_bp = Blueprint("tabular", __name__, template_folder="templates", url_prefix="/tabular")

# 3. Importa las rutas
# 2. Importa los modelos (¡para que la migración los vea!)
from . import models, routes
