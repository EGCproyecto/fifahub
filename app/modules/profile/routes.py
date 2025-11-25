from flask import jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.modules.auth.models import User
from app.modules.auth.services import AuthenticationService
from app.modules.dataset.models import BaseDataset, DataSet
from app.modules.profile import profile_bp
from app.modules.profile.forms import UserProfileForm
from app.modules.profile.services import UserProfileService


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    auth_service = AuthenticationService()
    profile = auth_service.get_authenticated_user_profile
    if not profile:
        return redirect(url_for("public.index"))

    form = UserProfileForm()
    if request.method == "POST":
        service = UserProfileService()
        result, errors = service.update_profile(profile.id, form)
        return service.handle_service_response(
            result,
            errors,
            "profile.edit_profile",
            "Profile updated successfully",
            "profile/edit.html",
            form,
        )

    return render_template("profile/edit.html", form=form)


@profile_bp.route("/profile/summary")
@login_required
def my_profile():
    page = request.args.get("page", 1, type=int)
    per_page = 5

    user_datasets_pagination = (
        db.session.query(DataSet)
        .filter(DataSet.user_id == current_user.id)
        .order_by(DataSet.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    total_datasets_count = db.session.query(DataSet).filter(DataSet.user_id == current_user.id).count()

    print(user_datasets_pagination.items)

    return render_template(
        "profile/summary.html",
        user_profile=current_user.profile,
        user=current_user,
        datasets=user_datasets_pagination.items,
        pagination=user_datasets_pagination,
        total_datasets=total_datasets_count,
    )


def serialize_dataset(dataset):
    """
    Convierte un objeto BaseDataset (UVL o Tabular) en un diccionario
    que luego se devuelve como JSON.
    Ahora incluye una 'view_url' para que el frontend pueda enlazar.
    """

    if dataset.type == "uvl":
        try:
            data = dataset.to_dict()
            data["type"] = "uvl"

            # --- LÍNEA NUEVA ---
            # Replicamos la lógica de summary.html: usamos la URL del DOI si existe,
            # si no, usamos la URL interna (data.get('url') es el DOI).
            data["view_url"] = data.get("url") or url_for("dataset.get_unsynchronized_dataset", dataset_id=dataset.id)

            return data
        except Exception as e:
            print(f"Error al serializar UVLDataset {dataset.id}: {e}")
            pass

    if dataset.type == "tabular":

        def get_cleaned_publication_type(ds_meta):
            if not ds_meta.publication_type:
                return "Other"
            return ds_meta.publication_type.name.replace("_", " ").title()

        return {  # como el tipo tabular no tiene la funcion .to_didct() la hacemos a mano
            "type": "tabular",
            "title": dataset.ds_meta_data.title,
            "id": dataset.id,
            "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
            "created_at_timestamp": int(dataset.created_at.timestamp()) if dataset.created_at else None,
            "description": dataset.ds_meta_data.description,
            "authors": [author.to_dict() for author in dataset.ds_meta_data.authors],
            "publication_type": get_cleaned_publication_type(dataset.ds_meta_data),
            "publication_doi": dataset.ds_meta_data.publication_doi,
            "dataset_doi": dataset.ds_meta_data.dataset_doi,
            "tags": dataset.ds_meta_data.tags.split(",") if dataset.ds_meta_data.tags else [],
            "download": f'{request.host_url.rstrip("/")}/dataset/download/{dataset.id}',
            "url": None,
            "zenodo": None,
            "files_count": None,
            "n_rows": dataset.meta_data.n_rows if dataset.meta_data else None,
            "n_cols": dataset.meta_data.n_cols if dataset.meta_data else None,
            "delimiter": dataset.meta_data.delimiter if dataset.meta_data else None,
            "encoding": dataset.meta_data.encoding if dataset.meta_data else None,
            "null_ratio": dataset.metrics.null_ratio if dataset.metrics else None,
            # --- LÍNEA NUEVA ---
            # Asumimos que los datasets tabulares usan la misma vista de detalle
            "view_url": url_for("dataset.get_unsynchronized_dataset", dataset_id=dataset.id),
        }

    # --- Fallback (opción de seguridad) ---
    return {
        "type": dataset.type,
        "id": dataset.id,
        "title": dataset.ds_meta_data.title if dataset.ds_meta_data else "N/A",
        "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
        "description": dataset.ds_meta_data.description if dataset.ds_meta_data else "",
        # --- LÍNEA NUEVA ---
        "view_url": url_for("dataset.get_unsynchronized_dataset", dataset_id=dataset.id),
    }


@profile_bp.route("/api/users/<string:userId>/datasets", methods=["GET"])
@login_required  # Esto sirve para que sea necesario estar loggeado para ver los datasets
def get_user_datasets_api(userId):
    """
    Endpoint API para obtener los datasets (UVL y Tabular) de un usuario.
    Devuelve una respuesta JSON con paginación.
    """

    user = db.session.query(User).filter_by(id=userId).first()
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 5, type=int)

    pagination = (
        db.session.query(BaseDataset)
        .filter(BaseDataset.user_id == userId)
        .order_by(BaseDataset.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    datasets_list = [serialize_dataset(dataset) for dataset in pagination.items]

    return jsonify(
        {
            "status": "success",
            "data": datasets_list,
            "pagination": {
                "total_items": pagination.total,
                "total_pages": pagination.pages,
                "current_page": pagination.page,
                "per_page": pagination.per_page,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
        }
    )


@profile_bp.route("/users/<string:userId>/datasets", methods=["GET"])
@login_required
def view_user_datasets(userId):
    """
    Renderiza la página de perfil público que listará los datasets
    de un usuario dado.
    """
    user_to_view = db.session.query(User).filter_by(id=userId).first()
    if not user_to_view:
        return "User not found", 404

    return render_template("profile/user_dataset_list.html", user_to_view=user_to_view)
