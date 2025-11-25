# Asegúrate de crear el parcial de plantilla en la ruta indicada más abajo.
from __future__ import annotations

from typing import Mapping, Tuple


class TabularDetailRenderer:
    def render(self, dataset):
        """
        Renderiza la vista de detalle usando el template específico de tabular.
        """
        meta = dataset.meta_data

        return (
            "modules/tabular/_detail_tabular.html",
            {
                "dataset": dataset,
                "meta": meta,
            },
        )


class TabularFacetProvider:
    def get_facets(self):
        return {
            "dtype": ["int", "float", "string", "bool"],
            "has_nulls": ["yes", "no"],
        }
