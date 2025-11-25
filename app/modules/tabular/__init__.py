# app/modules/tabular/__init__.py
"""Módulo Tabular: lógica y vistas para datasets CSV."""

from core.blueprints.base_blueprint import BaseBlueprint

tabular_bp = BaseBlueprint("tabular", __name__, template_folder="templates", url_prefix="/tabular")


from . import models, routes
