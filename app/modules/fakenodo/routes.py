from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.modules.dataset.models import DataSet
from app.modules.fakenodo.services import FakenodoService
from app.modules.featuremodel.models import FeatureModel

# Blueprint
fakenodo_bp = Blueprint("fakenodo", __name__, url_prefix="/api/fakenodo")


# -------------------------------------------------------------
# Create a new deposition (POST)
# -------------------------------------------------------------
@fakenodo_bp.route("/depositions", methods=["POST"])
@login_required
def create_deposition():
    try:
        dataset_id = request.json.get("dataset_id")
        dataset = DataSet.query.get(dataset_id)
        if not dataset:
            return jsonify({"status": "error", "message": "Dataset not found"}), 404

        service = FakenodoService()
        deposition = service.create_new_deposition(dataset)
        return jsonify({"status": "success", "deposition": deposition}), 201

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# -------------------------------------------------------------
# Upload CSV file (PUT)
# -------------------------------------------------------------
@fakenodo_bp.route("/depositions/<int:deposition_id>/files", methods=["PUT"])
@login_required
def upload_csv(deposition_id):
    try:
        dataset_id = request.form.get("dataset_id")
        feature_model_id = request.form.get("feature_model_id")

        dataset = DataSet.query.get(dataset_id)
        feature_model = FeatureModel.query.get(feature_model_id)
        if not dataset or not feature_model:
            return (
                jsonify(
                    {"status": "error", "message": "Dataset or FeatureModel not found"}
                ),
                404,
            )

        service = FakenodoService()
        result = service.upload_file(dataset, deposition_id, feature_model)

        return jsonify({"status": "success", "result": result}), 201

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# -------------------------------------------------------------
# Publish deposition (POST)
# -------------------------------------------------------------
@fakenodo_bp.route("/depositions/<int:deposition_id>/actions/publish", methods=["POST"])
@login_required
def publish_deposition(deposition_id):
    try:
        service = FakenodoService()
        result = service.publish_deposition(deposition_id)
        return jsonify({"status": "success", "result": result}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# -------------------------------------------------------------
# List all depositions(GET)
# -------------------------------------------------------------
@fakenodo_bp.route("/depositions", methods=["GET"])
@login_required
def list_depositions():
    try:
        service = FakenodoService()
        all_depositions = service.get_all_depositions()
        return jsonify({"status": "success", "depositions": all_depositions}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# -------------------------------------------------------------
# Get a specific deposition (GET)
# -------------------------------------------------------------
@fakenodo_bp.route("/depositions/<int:deposition_id>", methods=["GET"])
@login_required
def get_deposition(deposition_id):
    try:
        service = FakenodoService()
        deposition = service.get_deposition(deposition_id)
        return jsonify({"status": "success", "deposition": deposition}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# -------------------------------------------------------------
# Delete a deposition (DELETE)
# -------------------------------------------------------------
@fakenodo_bp.route("/depositions/<int:deposition_id>", methods=["DELETE"])
@login_required
def delete_deposition(deposition_id):
    try:
        service = FakenodoService()
        result = service.delete_deposition(deposition_id)
        return jsonify({"status": "success", "result": result}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
