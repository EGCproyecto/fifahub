from __future__ import annotations

from app.modules.tabular.forms import TabularDatasetForm
from app.modules.tabular.ingest import TabularIngestor
from app.modules.tabular.renderers import TabularDetailRenderer, TabularFacetProvider
from app.modules.uvl.forms import UVLDatasetForm
from app.modules.uvl.renderers import UVLDetailRenderer

from .interfaces import DatasetTypeSpec
from .registry import registry


def register_dataset_types(resolve_path_func=None) -> None:
    registry.register(
        DatasetTypeSpec(
            type_key="tabular",
            form_class=TabularDatasetForm,
            ingestor=TabularIngestor(resolve_path=resolve_path_func),
            validator=_NoopValidator(),
            detail_renderer=TabularDetailRenderer(),
            facets=(TabularFacetProvider(),),
        )
    )
    registry.register(
        DatasetTypeSpec(
            type_key="uvl",
            form_class=UVLDatasetForm,
            ingestor=_NoopIngestor(),
            validator=_NoopValidator(),
            detail_renderer=UVLDetailRenderer(),
            facets=(),
        )
    )


class _NoopValidator:
    def validate(self, payload):
        return None


class _NoopIngestor:
    def ingest(self, **kwargs):
        return {"status": "noop"}
