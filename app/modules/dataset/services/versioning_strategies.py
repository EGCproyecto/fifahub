import csv
from pathlib import Path


class TabularVersionStrategy:
    """Estrategia para datasets tabulares (CSV).
    Crea un snapshot con métricas básicas (filas, columnas, tamaño).
    """

    def snapshot(self, dataset):
        from app.modules.hubfile.services import HubfileService

        hsvc = HubfileService()
        summary, total_rows, max_cols = [], 0, 0

        for fm in dataset.feature_models:
            for f in fm.files:
                if not f.name.lower().endswith(".csv"):
                    continue

                path = Path(hsvc.get_path_by_hubfile(f))
                n_rows, n_cols = 0, None
                if path.exists():
                    try:
                        with path.open("r", encoding="utf-8", newline="") as fh:
                            reader = csv.reader(fh)
                            for i, row in enumerate(reader):
                                if i == 0:
                                    n_cols = len(row)
                                n_rows += 1
                    except Exception:
                        pass

                total_rows += n_rows
                max_cols = max(max_cols, n_cols or 0)
                summary.append(
                    {
                        "file": f.name,
                        "rows": n_rows,
                        "columns": n_cols,
                        "size": getattr(f, "size", None),
                    }
                )

        return {
            "type": "tabular",
            "metrics": {"total_rows": total_rows, "max_columns": max_cols},
            "files": summary,
        }


class UVLVersionStrategy:
    """Estrategia para datasets UVL.
    Captura snapshot con metadatos de tamaño (caracteres) por archivo.
    """

    def snapshot(self, dataset):
        from app.modules.hubfile.services import HubfileService

        hsvc = HubfileService()
        summary = []

        for fm in dataset.feature_models:
            for f in fm.files:
                if not f.name.lower().endswith(".uvl"):
                    continue

                path = Path(hsvc.get_path_by_hubfile(f))
                chars = 0
                if path.exists():
                    try:
                        chars = len(path.read_text(encoding="utf-8", errors="ignore"))
                    except Exception:
                        pass

                summary.append(
                    {
                        "file": f.name,
                        "chars": chars,
                        "size": getattr(f, "size", None),
                    }
                )

        return {"type": "uvl", "files": summary}
