from __future__ import annotations

from typing import Mapping, Tuple


class UVLDetailRenderer:
    def render(self, dataset) -> Tuple[str, Mapping]:
        return ("modules/uvl/_detail_uvl.html", {"dataset": dataset})
