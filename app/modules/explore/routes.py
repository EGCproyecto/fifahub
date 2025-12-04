from flask import jsonify, render_template, request
from sqlalchemy import or_

from app import db
from app.modules.dataset.models import DSMetaData
from app.modules.dataset.services.resolvers import gather_facets, list_type_keys
from app.modules.explore import explore_bp
from app.modules.explore.forms import ExploreForm
from app.modules.explore.services import ExploreService
from app.modules.tabular.models import TabularDataset


@explore_bp.route("/explore", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        query = request.args.get("q", "").strip() or request.args.get("query", "").strip()
        dataset_type = request.args.get("type", "any").lower()
        form = ExploreForm()
        dataset_types = list_type_keys()
        facets = gather_facets(dataset_type) if dataset_type != "any" else {}

        tabular_results = []
        if query:
            tabular_results = (
                db.session.query(TabularDataset)
                .join(DSMetaData, TabularDataset.ds_meta_data_id == DSMetaData.id)
                .filter(
                    or_(
                        DSMetaData.title.ilike(f"%{query}%"),
                        DSMetaData.description.ilike(f"%{query}%"),
                    )
                )
                .order_by(TabularDataset.id.desc())
                .all()
            )
        else:
            tabular_results = (
                db.session.query(TabularDataset)
                .join(DSMetaData, TabularDataset.ds_meta_data_id == DSMetaData.id)
                .order_by(TabularDataset.id.desc())
                .limit(5)
                .all()
            )

        return render_template(
            "explore/index.html",
            form=form,
            query=query,
            dataset_types=dataset_types,
            facets=facets,
            type_key=dataset_type,
            tabular_results=tabular_results,
        )

    if request.method == "POST":
        criteria = request.get_json() or {}
        dataset_type = criteria.pop("dataset_type", "any")
        facets = criteria.pop("facets", {}) or {}
        datasets = ExploreService().filter(dataset_type=dataset_type, facets=facets, **criteria)
        return jsonify([dataset.to_dict() for dataset in datasets])
