# app/modules/tabular/routes.py
from flask import Blueprint

tabular_bp = Blueprint("tabular", __name__, url_prefix="/tabular")


@tabular_bp.route("/upload")
def upload_tabular():
    return "Aquí irá la subida de CSVs de FIFA"
