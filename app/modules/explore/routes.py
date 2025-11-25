from flask import jsonify, render_template, request

from app.modules.dataset.services.resolvers import gather_facets, list_type_keys
from app.modules.explore import explore_bp
from app.modules.explore.forms import ExploreForm
from app.modules.explore.services import ExploreService


@explore_bp.route("/explore", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        query = request.args.get("query", "")
        dataset_type = request.args.get("type", "any").lower()
        form = ExploreForm()
        dataset_types = list_type_keys()
        facets = gather_facets(dataset_type) if dataset_type != "any" else {}
        return render_template(
            "explore/index.html",
            form=form,
            query=query,
            dataset_types=dataset_types,
            facets=facets,
            type_key=dataset_type,
        )

    if request.method == "POST":
        criteria = request.get_json() or {}
        dataset_type = criteria.pop("dataset_type", "any")
        facets = criteria.pop("facets", {}) or {}
        datasets = ExploreService().filter(dataset_type=dataset_type, facets=facets, **criteria)
        return jsonify([dataset.to_dict() for dataset in datasets])
