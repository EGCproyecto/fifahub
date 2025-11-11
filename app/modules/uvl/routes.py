from __future__ import annotations

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.modules.dataset.models import DSMetaData, PublicationType, UVLDataset
from app.modules.dataset.services.resolvers import resolve_ingestor, resolve_validator

from .forms import UVLDatasetForm

uvl_bp = Blueprint("uvl", __name__, template_folder="templates", url_prefix="/uvl")


@uvl_bp.route("/health", methods=["GET"])
def health():
    # Endpoint mínimo para que el blueprint esté “vivo”
    return jsonify({"status": "ok", "module": "uvl"})


@uvl_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_uvl():
    form = UVLDatasetForm()

    if request.method == "GET":
        return render_template("modules/uvl/upload_uvl.html", form=form)

    if not form.validate_on_submit():
        return render_template("modules/uvl/upload_uvl.html", form=form), 400

    validator = resolve_validator("uvl")
    validation_error = validator.validate(request.form) if validator else None
    if validation_error:
        flash(validation_error, "danger")
        return render_template("modules/uvl/upload_uvl.html", form=form), 400

    ingestor = resolve_ingestor("uvl")
    parsed_payload = ingestor.ingest(request=request, form=form) if ingestor else {}

    meta = DSMetaData(
        title=form.name.data,
        description=parsed_payload.get("description", "UVL dataset"),
        publication_type=PublicationType.NONE,
        tags=parsed_payload.get("tags", "uvl"),
    )
    db.session.add(meta)
    db.session.flush()

    dataset = UVLDataset(user_id=current_user.id, ds_meta_data_id=meta.id)
    db.session.add(dataset)
    db.session.commit()

    flash("UVL dataset created successfully", "success")
    return redirect(url_for("dataset.view_dataset", dataset_id=dataset.id))
