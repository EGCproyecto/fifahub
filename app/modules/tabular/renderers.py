# Asegúrate de crear el parcial de plantilla en la ruta indicada más abajo.
from __future__ import annotations

from typing import Mapping, Tuple


class TabularDetailRenderer:
    def render(self, dataset) -> Tuple[str, Mapping]:
        meta = getattr(dataset, "meta_data", None)
        # La ruta del template debe existir en tus loaders de Jinja (ver abajo).
        return (
            "modules/tabular/_detail_tabular.html",
            {"dataset": dataset, "meta": meta},
        )


class TabularFacetProvider:
    def get_facets(self):
        # Extiende con facetas reales cuando las tengas.
        return {"dtype": ["int", "float", "string", "bool"]}
