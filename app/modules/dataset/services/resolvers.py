from __future__ import annotations

from typing import Any

from .registry import registry


def resolve_form(type_key: str):
    return registry.get(type_key).form_class


def resolve_ingestor(type_key: str):
    return registry.get(type_key).ingestor


def resolve_validator(type_key: str):
    return registry.get(type_key).validator


def render_detail(type_key: str, dataset: Any):
    renderer = registry.get(type_key).detail_renderer
    template_name, ctx = renderer.render(dataset)
    return template_name, ctx


def list_type_keys():
    return registry.keys()


def gather_facets(type_key: str):
    spec = registry.get(type_key)
    merged = {}
    for fp in spec.facets:
        merged.update(fp.get_facets())
    return merged
