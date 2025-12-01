import json
import logging
import os
import shutil
import tempfile
import uuid
from zipfile import ZipFile

from flask import abort, jsonify, make_response, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required

from app import db
from app.modules.auth.services import FollowService
from app.modules.dataset import dataset_bp
from app.modules.dataset.forms import DataSetForm
from app.modules.dataset.models import Author, BaseDataset, DatasetVersion
from app.modules.dataset.services import (
    AuthorService,
    DataSetService,
    DOIMappingService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
)
from app.modules.dataset.services.recommendation_service import RecommendationService
from app.modules.dataset.services.resolvers import render_detail
from app.modules.zenodo.services import ZenodoService

logger = logging.getLogger(__name__)


dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
zenodo_service = ZenodoService()
doi_mapping_service = DOIMappingService()
ds_view_record_service = DSViewRecordService()
ds_download_record_service = DSDownloadRecordService()
ds_download_record_service = DSDownloadRecordService()
recommendation_service = RecommendationService()
follow_service = FollowService()


@dataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()
    if request.method == "POST":

        dataset = None

        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400

        try:
            logger.info("Creating dataset...")
            dataset = dataset_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset}")
            dataset_service.move_feature_models(dataset)
        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return (
                jsonify({"Exception while create dataset data in local: ": str(exc)}),
                400,
            )

        # send dataset as deposition to Zenodo
        data = {}
        try:
            zenodo_response_json = zenodo_service.create_new_deposition(dataset)
            response_data = json.dumps(zenodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            data = {}
            zenodo_response_json = {}
            logger.exception(f"Exception while create dataset data in Zenodo {exc}")

        if data.get("conceptrecid"):
            deposition_id = data.get("id")

            # update dataset with deposition id in Zenodo
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)

            try:
                # iterate for each feature model (one feature model = one request to Zenodo)
                for feature_model in dataset.feature_models:
                    zenodo_service.upload_file(dataset, deposition_id, feature_model)

                # publish deposition
                zenodo_service.publish_deposition(deposition_id)

                # update DOI
                deposition_doi = zenodo_service.get_doi(deposition_id)
                dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible upload feature models in Zenodo and update the DOI: {e}"
                return jsonify({"message": msg}), 200

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("dataset/upload_dataset.html", form=form)


@dataset_bp.route("/dataset/list", methods=["GET", "POST"])
@login_required
def list_dataset():
    return render_template(
        "dataset/list_datasets.html",
        datasets=dataset_service.get_synchronized(current_user.id),
        local_datasets=dataset_service.get_unsynchronized(current_user.id),
    )


@dataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload():
    file = request.files["file"]
    temp_folder = current_user.temp_folder()

    if not file or not file.filename.endswith(".uvl"):
        return jsonify({"message": "No valid file"}), 400

    # create temp folder
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    file_path = os.path.join(temp_folder, file.filename)

    if os.path.exists(file_path):
        # Generate unique filename (by recursion)
        base_name, extension = os.path.splitext(file.filename)
        i = 1
        while os.path.exists(os.path.join(temp_folder, f"{base_name} ({i}){extension}")):
            i += 1
        new_filename = f"{base_name} ({i}){extension}"
        file_path = os.path.join(temp_folder, new_filename)
    else:
        new_filename = file.filename

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({"message": str(e)}), 500

    return (
        jsonify(
            {
                "message": "UVL uploaded and validated successfully",
                "filename": new_filename,
            }
        ),
        200,
    )


@dataset_bp.route("/dataset/file/delete", methods=["POST"])
def delete():
    data = request.get_json()
    filename = data.get("file")
    temp_folder = current_user.temp_folder()
    filepath = os.path.join(temp_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"})

    return jsonify({"error": "Error: File not found"})


@dataset_bp.route("/dataset/download/<int:dataset_id>", methods=["GET"])
def download_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)

    file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"dataset_{dataset_id}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for subdir, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(subdir, file)

                relative_path = os.path.relpath(full_path, file_path)

                zipf.write(
                    full_path,
                    arcname=os.path.join(os.path.basename(zip_path[:-4]), relative_path),
                )

    user_cookie = request.cookies.get("download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())  # Generate a new unique identifier if it does not exist
        # Save the cookie to the user's browser
        resp = make_response(
            send_from_directory(
                temp_dir,
                f"dataset_{dataset_id}.zip",
                as_attachment=True,
                mimetype="application/zip",
            )
        )
        resp.set_cookie("download_cookie", user_cookie)
    else:
        resp = send_from_directory(
            temp_dir,
            f"dataset_{dataset_id}.zip",
            as_attachment=True,
            mimetype="application/zip",
        )

    try:
        ds_download_record_service.record_download(
            dataset=dataset,
            user_cookie=user_cookie,
            user_id=current_user.id if current_user.is_authenticated else None,
        )
        logger.info("Recorded download for dataset_id=%s; new_count=%s", dataset.id, dataset.download_count)
    except Exception:
        logger.exception("Failed to record download for dataset_id=%s", dataset.id)

    return resp


@dataset_bp.route("/datasets/<int:dataset_id>/stats", methods=["GET"])
def dataset_stats(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)
    views = ds_view_record_service.count_for_dataset(dataset.id)
    return jsonify(
        {
            "dataset_id": dataset.id,
            "downloads": dataset.download_count or 0,
            "views": views,
        }
    )


@dataset_bp.route("/dataset/view/<int:dataset_id>", methods=["GET"])
@login_required
def view_dataset(dataset_id: int):
    dataset = BaseDataset.query.get_or_404(dataset_id)

    if dataset.user_id != current_user.id:
        abort(403)

    detail_template, detail_ctx = render_detail(dataset.type, dataset)
    detail_ctx["related_datasets"] = recommendation_service.get_related_datasets(dataset.id)
    versions = DatasetVersion.query.filter_by(dataset_id=dataset.id).order_by(DatasetVersion.created_at.desc()).all()

    return render_template(
        "dataset/view_dataset.html",
        detail_template=detail_template,
        versions=versions,
        **detail_ctx,
    )


@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):

    # Check if the DOI is an old DOI
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        # Redirect to the same path with the new DOI
        return redirect(url_for("dataset.subdomain_index", doi=new_doi), code=302)

    # Try to search the dataset by the provided DOI (which should already be the new one)
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)

    if not ds_meta_data:
        abort(404)

    # Get dataset
    dataset = ds_meta_data.data_set

    # cookie de vistas
    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)

    # resolver de detalle (tu flujo original)
    detail_template, detail_ctx = render_detail(dataset.type, dataset)
    detail_ctx["related_datasets"] = recommendation_service.get_related_datasets(dataset.id)

    # 🔹 NUEVO: versiones ordenadas (últimas primero) y pasadas a la plantilla
    versions = DatasetVersion.query.filter_by(dataset_id=dataset.id).order_by(DatasetVersion.created_at.desc()).all()

    resp = make_response(
        render_template(
            "dataset/view_dataset.html",
            detail_template=detail_template,
            versions=versions,  # <- aquí van las versiones
            **detail_ctx,  # meta=..., dataset=..., etc.
        )
    )
    resp.set_cookie("view_cookie", user_cookie)

    return resp


@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
def get_unsynchronized_dataset(dataset_id):

    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)

    if not dataset:
        abort(404)

    detail_template, detail_ctx = render_detail(dataset.type, dataset)
    detail_ctx["related_datasets"] = recommendation_service.get_related_datasets(dataset.id)

    # 🔹 NUEVO: versiones también para no sincronizados (si existen)
    versions = DatasetVersion.query.filter_by(dataset_id=dataset.id).order_by(DatasetVersion.created_at.desc()).all()

    return render_template(
        "dataset/view_dataset.html",
        detail_template=detail_template,
        versions=versions,  # <- aquí van las versiones
        **detail_ctx,  # meta=..., dataset=..., etc.
    )


@dataset_bp.route("/authors/<int:author_id>", methods=["GET"])
def author_detail(author_id: int):
    author = Author.query.get_or_404(author_id)

    followers = follow_service.get_followers_for_author(author)
    author_follower_count = len(followers)

    is_following_author = False
    if current_user.is_authenticated:
        followed_authors = follow_service.get_followed_authors_for_user(current_user)
        is_following_author = any(a.id == author.id for a in followed_authors)

    return render_template(
        "dataset/author_detail.html",
        author=author,
        author_follower_count=author_follower_count,
        is_following_author=is_following_author,
    )


@dataset_bp.route("/communities/<string:community_id>", methods=["GET"])
def community_detail(community_id: str):
    community_identifier = (community_id or "").strip()
    if not community_identifier:
        abort(404)

    followers = follow_service.get_followers_for_community(community_identifier)
    community_follower_count = len(followers)

    is_following_community = False
    if current_user.is_authenticated:
        followed_communities = follow_service.get_followed_communities_for_user(current_user)
        is_following_community = community_identifier in followed_communities

    return render_template(
        "dataset/community_detail.html",
        community_id=community_identifier,
        community_follower_count=community_follower_count,
        is_following_community=is_following_community,
    )
