from __future__ import annotations

from typing import Dict

from .interfaces import DatasetTypeSpec


class DatasetTypeRegistry:
    def __init__(self) -> None:
        self._by_key: dict[str, DatasetTypeSpec] = {}

    def clear(self) -> None:
        """Vacía el registro (útil para tests que crean varias apps)."""
        self._by_key.clear()

    def register(self, spec: DatasetTypeSpec) -> None:
        """Registra un tipo. Si ya existe, lo reemplaza (idempotente)."""
        self._by_key[spec.type_key] = spec

    def get(self, type_key: str) -> DatasetTypeSpec:
        return self._by_key[type_key]

    def keys(self):
        return tuple(self._by_key.keys())


registry = DatasetTypeRegistry()


def dataset_type(spec_factory):
    spec = spec_factory()
    registry.register(spec)
    return spec_factory
