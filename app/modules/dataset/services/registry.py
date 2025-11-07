from __future__ import annotations

from typing import Dict

from .interfaces import DatasetTypeSpec


class DatasetTypeRegistry:
    def __init__(self) -> None:
        self._by_key: Dict[str, DatasetTypeSpec] = {}

    def register(self, spec: DatasetTypeSpec) -> None:
        key = spec.type_key
        if key in self._by_key:
            raise ValueError(f"Dataset type '{key}' ya registrado")
        self._by_key[key] = spec

    def get(self, key: str) -> DatasetTypeSpec:
        if key not in self._by_key:
            raise KeyError(f"Dataset type '{key}' no encontrado")
        return self._by_key[key]

    def keys(self):
        return tuple(self._by_key.keys())

    def all(self):
        return tuple(self._by_key.values())


registry = DatasetTypeRegistry()


def dataset_type(spec_factory):
    spec = spec_factory()
    registry.register(spec)
    return spec_factory
