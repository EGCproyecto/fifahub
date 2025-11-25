import os
import uuid
from datetime import datetime, timezone

from flask import current_app, jsonify, make_response, request, send_from_directory
from flask_login import current_user, login_required

from app import db
from app.modules.dataset.services.versioning_service import VersioningService
from app.modules.hubfile import hubfile_bp
from app.modules.hubfile.models import Hubfile, HubfileDownloadRecord, HubfileViewRecord
from app.modules.hubfile.services import HubfileDownloadRecordService, HubfileService


@hubfile_bp.route("/file/reupload/<int:file_id>", methods=["POST"])
@login_required
def reupload_csv(file_id):
    """
    Reemplaza un archivo CSV existente por una nueva versión del mismo.
    Tras la subida, recalcula métricas y crea una nueva versión del dataset.
    """
    hsvc = HubfileService()
    hf = hsvc.get_or_404(file_id)
    dataset = hf.feature_model.data_set

    file = request.files.get("file")
    if not file or not file.filename.lower().endswith(".csv"):
        return jsonify({"message": "CSV requerido"}), 400

    # Guardar físicamente
    path = hsvc.get_path_by_hubfile(hf)
    try:
        file.save(path)
    except Exception as e:
        return jsonify({"message": f"Error guardando CSV: {e}"}), 500

    # (Opcional) recalcular size/checksum según vuestro servicio
    try:
        file.seek(0, 2)  # Ir al final
        hf.size = file.tell()
    except Exception:
        pass
    db.session.commit()

    # Crear nueva versión con snapshot y métricas
    try:
        VersioningService().create_version(
            dataset=dataset,
            author_id=getattr(current_user, "id", None),
            change_note=f"Re-subida de {hf.name}",
            strategy="tabular",
        )
    except Exception as e:
        return jsonify({"message": f"CSV subido pero error en versionado: {e}"}), 500

    return jsonify({"message": "CSV re-subido y versionado correctamente"}), 200


@hubfile_bp.route("/file/download/<int:file_id>", methods=["GET"])
def download_file(file_id):
    file = HubfileService().get_or_404(file_id)
    filename = file.name

    directory_path = f"uploads/user_{file.feature_model.data_set.user_id}/dataset_{file.feature_model.data_set_id}/"
    parent_directory_path = os.path.dirname(current_app.root_path)
    file_path = os.path.join(parent_directory_path, directory_path)

    # Obtener cookie o crear una nueva
    user_cookie = request.cookies.get("file_download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())

    # Registrar descarga si no existe
    existing_record = HubfileDownloadRecord.query.filter_by(
        user_id=current_user.id if current_user.is_authenticated else None,
        file_id=file_id,
        download_cookie=user_cookie,
    ).first()

    if not existing_record:
        HubfileDownloadRecordService().create(
            user_id=current_user.id if current_user.is_authenticated else None,
            file_id=file_id,
            download_date=datetime.now(timezone.utc),
            download_cookie=user_cookie,
        )

    # Respuesta con cookie persistente
    resp = make_response(send_from_directory(directory=file_path, path=filename, as_attachment=True))
    resp.set_cookie("file_download_cookie", user_cookie)

    return resp


@hubfile_bp.route("/file/view/<int:file_id>", methods=["GET"])
def view_file(file_id):
    file = HubfileService().get_or_404(file_id)
    filename = file.name

    directory_path = f"uploads/user_{file.feature_model.data_set.user_id}/dataset_{file.feature_model.data_set_id}/"
    parent_directory_path = os.path.dirname(current_app.root_path)
    file_path = os.path.join(parent_directory_path, directory_path, filename)

    try:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                content = f.read()

            user_cookie = request.cookies.get("view_cookie")
            if not user_cookie:
                user_cookie = str(uuid.uuid4())

            existing_record = HubfileViewRecord.query.filter_by(
                user_id=current_user.id if current_user.is_authenticated else None,
                file_id=file_id,
                view_cookie=user_cookie,
            ).first()

            if not existing_record:
                new_view_record = HubfileViewRecord(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    file_id=file_id,
                    view_date=datetime.now(),
                    view_cookie=user_cookie,
                )
                db.session.add(new_view_record)
                db.session.commit()

            response = jsonify({"success": True, "content": content})
            if not request.cookies.get("view_cookie"):
                response = make_response(response)
                response.set_cookie("view_cookie", user_cookie, max_age=60 * 60 * 24 * 365 * 2)

            return response
        else:
            return jsonify({"success": False, "error": "File not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
