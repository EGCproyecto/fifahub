from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.modules.dataset.repositories import DataSetRepository
from app.modules.fakenodo.services import FakenodoService

bp = Blueprint("fakenodo", __name__, url_prefix="/fakenodo")

fakenodo_service = FakenodoService()
dataset_repo = DataSetRepository()


@bp.route("/depositions", methods=["POST"])
@login_required
def create_deposition():
    data = request.get_json() or {}
    ds_id = data.get("dataset_id")
    publication_doi = data.get("publication_doi")

    if ds_id is None:
        return jsonify({"error": "dataset_id is required"}), 400

    dataset = dataset_repo.get_by_id(ds_id)
    if dataset is None:
        return jsonify({"error": f"Dataset {ds_id} not found"}), 404

    resp = fakenodo_service.create_new_deposition(dataset, publication_doi=publication_doi)
    return jsonify(resp), 201


@bp.route("/depositions/<int:dep_id>/upload", methods=["POST"])
@login_required
def upload_file(dep_id: int):
    data = request.get_json() or {}
    ds_id = data.get("dataset_id")
    # feature_model_id = data.get("feature_model_id")

    dataset = dataset_repo.get_by_id(ds_id)
    if dataset is None:
        return jsonify({"error": f"Dataset {ds_id} not found"}), 404

    resp = fakenodo_service.upload_file(dataset, dep_id, feature_model=None)
    return jsonify(resp), 200


@bp.route("/depositions/<int:dep_id>/publish", methods=["POST"])
@login_required
def publish_deposition(dep_id: int):
    resp = fakenodo_service.publish_deposition(dep_id)
    return jsonify(resp), 200


@bp.route("/depositions/<int:dep_id>", methods=["DELETE"])
@login_required
def delete_deposition(dep_id: int):
    resp = fakenodo_service.delete_deposition(dep_id)
    return jsonify(resp), 200
