import os
import uuid

from flask import abort, current_app, flash, render_template, request
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app import db
from app.modules.dataset.models import DSMetaData, PublicationType

from . import tabular_bp
from .forms import TabularDatasetForm
from .ingest import TabularIngestor
from .models import TabularDataset
from .renderers import TabularDetailRenderer

try:
    from ..dataset.services.versioning_service import VersioningService  # type: ignore
except Exception:  # pragma: no cover
    VersioningService = None  # type: ignore


def _uploads_dir() -> str:
    base = current_app.config.get(
        "UPLOAD_FOLDER",
        os.path.abspath(os.path.join(current_app.root_path, "..", "..", "var", "uploads")),
    )
    os.makedirs(base, exist_ok=True)
    return base


def _save_uploaded_file(file_storage) -> str:
    filename = secure_filename(file_storage.filename or f"upload-{uuid.uuid4().hex}.csv")
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
    """Subida e ingesta de CSV tabular"""
    form = TabularDatasetForm()

    if request.method == "GET":
        return render_template("modules/tabular/upload_tabular.html", form=form)

    if not form.validate_on_submit():
        return render_template("modules/tabular/upload_tabular.html", form=form), 400

    f = form.csv_file.data
    if not f or not f.filename:
        flash("Sube un archivo CSV válido.", "warning")
        return render_template("modules/tabular/upload_tabular.html", form=form), 400

    try:
        file_path = _save_uploaded_file(f)
    except ValueError as e:
        flash(str(e), "danger")
        return render_template("modules/tabular/upload_tabular.html", form=form), 400

    name = (form.name.data or "").strip()

    ds_md = DSMetaData(
        title=name or "Tabular dataset",
        description="CSV importado",
        publication_type=PublicationType.OTHER,
    )
    db.session.add(ds_md)
    db.session.flush()

    dataset = (
        TabularDataset.query.filter_by(user_id=current_user.id)
        .join(DSMetaData, TabularDataset.ds_meta_data_id == DSMetaData.id)
        .filter(DSMetaData.title == ds_md.title)
        .first()
    )
    is_resubida = dataset is not None

    if dataset is None:
        dataset = TabularDataset(
            user_id=current_user.id,
            ds_meta_data_id=ds_md.id,
            rows_count=None,
        )
        db.session.add(dataset)
        db.session.flush()

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
        return render_template("modules/tabular/upload_tabular.html", form=form), 400

    if is_resubida and VersioningService is not None:
        try:
            VersioningService.create_new_version(dataset_id=dataset.id, note="Re-subida CSV (tabular)")
        except Exception:
            flash("Aviso: no se pudo registrar la nueva versión.", "warning")

    db.session.commit()

    renderer = TabularDetailRenderer()
    template, ctx = renderer.render(dataset)
    return render_template(template, **ctx), 201


@tabular_bp.route("/my", methods=["GET"])
@login_required
def my_tabular():
    """Listado de tabulares del usuario"""
    items = TabularDataset.query.filter_by(user_id=current_user.id).order_by(TabularDataset.id.desc()).all()
    return render_template("modules/tabular/list_tabular.html", items=items)


@tabular_bp.route("/<int:dataset_id>", methods=["GET"])
@login_required
def detail(dataset_id: int):
    """Vista de detalle de un tabular"""
    dataset = TabularDataset.query.filter_by(id=dataset_id, user_id=current_user.id).first()
    if not dataset:
        abort(404)
    renderer = TabularDetailRenderer()
    template, ctx = renderer.render(dataset)
    return render_template(template, **ctx)
