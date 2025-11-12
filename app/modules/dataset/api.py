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

    @bp.route("/api/datasets/<int:dataset_id>", methods=["GET"])
    def dataset_detail(dataset_id):
        dataset = BaseDataset.query.get_or_404(dataset_id)
        data = {
            "id": dataset.id,
            "type": dataset.type,
            "title": dataset.ds_meta_data.title if dataset.ds_meta_data else None,
            "download_count": dataset.download_count or 0,
        }
        if dataset.type == "tabular":
            data["rows_count"] = getattr(dataset, "rows_count", None)
            data["schema"] = getattr(dataset, "schema_json", None)
        return jsonify(data)
