from flask import jsonify

from app.modules.dataset.models import BaseDataset


def init_blueprint_api(bp):
    @bp.route("/api/datasets-polymorphic", methods=["GET"])
    def list_polymorphic():
        items = BaseDataset.query.order_by(BaseDataset.id.desc()).all()

        def as_dict(ds):
            data = {
                "id": ds.id,
                "type": ds.type,
                "title": ds.ds_meta_data.title if ds.ds_meta_data else None,
            }
            if ds.type == "tabular":
                data["rows_count"] = getattr(ds, "rows_count", None)
            return data

        return jsonify([as_dict(x) for x in items])
