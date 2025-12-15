import os
import shutil
import uuid

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app import db
from app.modules.dataset.models import Author, DSMetaData, PublicationType
from app.modules.dataset.services.notification_service import notification_service
from app.modules.recommendation.service import RecommendationService

from . import tabular_bp
from .forms import TabularDatasetForm
from .ingest import TabularIngestor
from .models import TabularDataset

try:
    from ..dataset.services.versioning_service import VersioningService  # type: ignore
except Exception:
    VersioningService = None  # type: ignore


def _uploads_dir() -> str:
    base = current_app.config.get(
        "UPLOAD_FOLDER",
        os.path.abspath(os.path.join(current_app.root_path, "..", "..", "var", "uploads")),
    )
    os.makedirs(base, exist_ok=True)
    return base


def _save_uploaded_file(file_storage) -> str:
    original = secure_filename(file_storage.filename or "")
    base, ext = os.path.splitext(original)
    base = base or "upload"
    ext = ext or ".csv"
    filename = f"{base}-{uuid.uuid4().hex}{ext}"
    path = os.path.join(_uploads_dir(), filename)
    file_storage.save(path)
    if os.path.getsize(path) == 0:
        try:
            os.remove(path)
        finally:
            pass
        raise ValueError("El archivo está vacío.")
    return path


@tabular_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    form = TabularDatasetForm()

    if request.method == "GET":
        # Pre-fill author name with current user's name
        if current_user.profile:
            form.author_name.data = f"{current_user.profile.name} {current_user.profile.surname}".strip()
        return render_template("upload_tabular.html", form=form)

    if not form.validate_on_submit():
        return render_template("upload_tabular.html", form=form), 400

    f = form.csv_file.data
    if not f or not f.filename:
        flash("Sube un archivo CSV válido.", "warning")
        return render_template("upload_tabular.html", form=form), 400

    try:
        file_path = _save_uploaded_file(f)
    except ValueError as e:
        flash(str(e), "danger")
        return render_template("upload_tabular.html", form=form), 400

    name = (form.name.data or "").strip()
    title_value = name or "Tabular dataset"

    dataset = (
        TabularDataset.query.filter_by(user_id=current_user.id)
        .join(DSMetaData, TabularDataset.ds_meta_data_id == DSMetaData.id)
        .filter(DSMetaData.title == title_value)
        .first()
    )
    is_resubida = dataset is not None

    if dataset is None:
        ds_md = DSMetaData(
            title=title_value,
            description="CSV importado",
            publication_type=PublicationType.OTHER,
        )
        db.session.add(ds_md)
        db.session.flush()

        dataset = TabularDataset(
            user_id=current_user.id,
            ds_meta_data_id=ds_md.id,
            rows_count=None,
        )
        db.session.add(dataset)
        db.session.flush()
    else:
        ds_md = dataset.ds_meta_data

    if ds_md is not None:
        # Handle author from name input
        author_name_input = (form.author_name.data or "").strip()
        if author_name_input:
            # Create new Author for this dataset
            author = Author(name=author_name_input, ds_meta_data_id=ds_md.id)
            db.session.add(author)
            current_app.logger.info(
                "Created new author '%s' for dataset ds_meta_data_id=%s",
                author_name_input,
                ds_md.id,
            )

        community_id = (form.community_id.data or "").strip()
        if community_id:
            existing_tags = [tag.strip() for tag in (ds_md.tags or "").split(",") if tag.strip()]
            community_tag = f"community:{community_id}"
            if community_tag not in existing_tags:
                existing_tags.append(community_tag)
            ds_md.tags = ",".join(existing_tags) if existing_tags else None

    ingestor = TabularIngestor(resolve_path=lambda hubfile_id: hubfile_id)
    try:
        ingestor.ingest(
            dataset_id=dataset.id,
            file_path=file_path,
            delimiter=(form.delimiter.data if form.delimiter.data != "\\t" else "\t"),
            has_header=bool(form.has_header.data),
            sample_rows=int(form.sample_rows.data or 20),
        )
    except Exception as e:
        current_app.logger.exception("Falló la ingesta tabular")
        flash(f"Error al procesar el CSV: {e}", "danger")
        db.session.rollback()
        return render_template("upload_tabular.html", form=form), 400

    storage_dir = os.path.join(_uploads_dir(), f"user_{dataset.user_id}", f"dataset_{dataset.id}")
    os.makedirs(storage_dir, exist_ok=True)
    dest_path = os.path.join(storage_dir, os.path.basename(file_path))
    try:
        shutil.move(file_path, dest_path)
    except Exception as exc:
        current_app.logger.exception("No se pudo preparar el archivo para su descarga")
        flash(f"Error al guardar el CSV definitivo: {exc}", "danger")
        db.session.rollback()
        return render_template("upload_tabular.html", form=form), 400

    if is_resubida and VersioningService is not None:
        try:
            VersioningService.create_new_version(dataset_id=dataset.id, note="Re-subida CSV (tabular)")
        except Exception:
            flash("Aviso: no se pudo registrar la nueva versión.", "warning")

    db.session.commit()

    notification_service.trigger_new_dataset_notifications_async(dataset)

    return redirect(url_for("tabular.detail", dataset_id=dataset.id))


@tabular_bp.route("/my", methods=["GET"])
@login_required
def my_tabular():
    items = TabularDataset.query.filter_by(user_id=current_user.id).order_by(TabularDataset.id.desc()).all()
    return render_template("list_tabular.html", items=items)


@tabular_bp.route("/<int:dataset_id>", methods=["GET"])
@login_required
def detail(dataset_id: int):
    dataset = TabularDataset.query.filter_by(id=dataset_id).first()
    if not dataset:
        abort(404)
    tabular_recommendations = RecommendationService.get_related_datasets(dataset.id)
    return render_template("view_tabular.html", dataset=dataset, tabular_recommendations=tabular_recommendations)
