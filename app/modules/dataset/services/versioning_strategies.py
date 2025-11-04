# app/modules/dataset/services/versioning_strategies.py
from abc import ABC, abstractmethod
from pathlib import Path
import csv

class BaseVersionStrategy(ABC):
    @abstractmethod
    def snapshot(self, dataset) -> dict:
        ...

class TabularVersionStrategy(BaseVersionStrategy):
    """Snapshot por hubfiles CSV + métricas básicas (filas totales, columnas máx)."""

    def snapshot(self, dataset) -> dict:
        from app.modules.hubfile.services import HubfileService
        files = [f for fm in dataset.feature_models for f in fm.files if f.name.lower().endswith(".csv")]
        hsvc = HubfileService()

        summary, total_rows, max_cols = [], 0, 0
        for f in files:
            path = Path(hsvc.get_path_by_hubfile(f))
            n_rows, n_cols = 0, None
            if path.exists():
                try:
                    with path.open("r", newline="", encoding="utf-8") as fh:
                        reader = csv.reader(fh)
                        for i, row in enumerate(reader):
                            if i == 0:
                                n_cols = len(row)
                            n_rows += 1
                except Exception:
                    pass
            total_rows += n_rows
            max_cols = max(max_cols, n_cols or 0)
            summary.append({"file": f.name, "rows": n_rows, "columns": n_cols, "size": getattr(f, "size", None)})
        return {"type": "tabular", "files": summary, "metrics": {"total_rows": total_rows, "max_columns": max_cols}}

class UVLVersionStrategy(BaseVersionStrategy):
    """Snapshot UVL con metadatos ligeros (longitud del contenido)."""

    def snapshot(self, dataset) -> dict:
        from app.modules.hubfile.services import HubfileService
        files = [f for fm in dataset.feature_models for f in fm.files if f.name.lower().endswith(".uvl")]
        hsvc = HubfileService()

        summary = []
        for f in files:
            path = Path(hsvc.get_path_by_hubfile(f))
            chars = None
            if path.exists():
                try:
                    chars = len(path.read_text(encoding="utf-8", errors="ignore"))
                except Exception:
                    pass
            summary.append({"file": f.name, "chars": chars, "size": getattr(f, "size", None)})
        return {"type": "uvl", "files": summary}
