from __future__ import annotations

from flask import Blueprint, jsonify

uvl_bp = Blueprint("uvl", __name__, url_prefix="/uvl")


@uvl_bp.route("/health", methods=["GET"])
def health():
    # Endpoint mínimo para que el blueprint esté “vivo”
    return jsonify({"status": "ok", "module": "uvl"})
