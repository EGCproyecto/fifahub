from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence, Tuple


class FormLike(Protocol):
    def validate_on_submit(self) -> bool: ...


class Ingestor(Protocol):
    def ingest(self, **kwargs) -> Mapping[str, Any]: ...


class Validator(Protocol):
    def validate(self, payload: Mapping[str, Any]) -> None: ...


class DetailRenderer(Protocol):
    def render(self, dataset: Any) -> Tuple[str, Mapping[str, Any]]: ...


class FacetProvider(Protocol):
    def get_facets(self) -> Mapping[str, Sequence[Any]]: ...


@dataclass(frozen=True, slots=True)
class DatasetTypeSpec:
    type_key: str
    form_class: type[FormLike]
    ingestor: Ingestor
    validator: Validator
    detail_renderer: DetailRenderer
    facets: Sequence[FacetProvider] = ()
