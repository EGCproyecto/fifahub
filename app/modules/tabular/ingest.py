# OJO: si llamas con hubfile_id debes registrar un resolve_path en type_registration; si no, pasa file_path.
# OJO: TabularMetaData.dataset_id y TabularMetrics.dataset_id son 1-1; reingesta sin limpiar/actualizar romperá por UNIQUE.
from __future__ import annotations

from statistics import mean
from typing import Any, Callable, Mapping, Optional

from app import db
from app.modules.tabular.models import TabularColumn, TabularMetaData, TabularMetrics
from app.modules.tabular.utils.parser import parse_csv_metadata


class TabularIngestor:
    def __init__(self, resolve_path: Optional[Callable[[int], str]] = None) -> None:
        self._resolve_path = resolve_path  # pásame aquí tu HubfileService cuando lo tengas.

    def ingest(
        self,
        *,
        dataset_id: int,
        file_path: Optional[str] = None,
        hubfile_id: Optional[int] = None,
        delimiter: str = ",",
        has_header: bool = True,
        sample_rows: int = 5,
    ) -> Mapping[str, Any]:
        if not file_path:
            if not (hubfile_id and self._resolve_path):
                raise ValueError("Debes pasar file_path o un hubfile_id con resolve_path definido.")
            file_path = self._resolve_path(hubfile_id)

        existing_meta = TabularMetaData.query.filter_by(dataset_id=dataset_id).first()
        existing_metrics = TabularMetrics.query.filter_by(dataset_id=dataset_id).first()
        if existing_meta:
            db.session.delete(existing_meta)
        if existing_metrics:
            db.session.delete(existing_metrics)
        if existing_meta or existing_metrics:
            db.session.flush()

        parsed = parse_csv_metadata(
            file_path=file_path,
            delimiter=delimiter,
            has_header=has_header,
            sample_rows=sample_rows,
        )

        meta = TabularMetaData(
            dataset_id=dataset_id,
            hubfile_id=hubfile_id,
            delimiter=parsed.get("delimiter", delimiter),
            encoding=parsed.get("encoding", "utf-8"),
            has_header=parsed.get("has_header", has_header),
            n_rows=parsed.get("n_rows", 0),
            n_cols=parsed.get("n_cols", 0),
            primary_keys=parsed.get("primary_keys"),
            index_cols=parsed.get("index_cols"),
            sample_rows=parsed.get("sample_rows", []),
        )
        db.session.add(meta)
        db.session.flush()  # meta.id disponible

        for col in parsed.get("columns", []):
            db.session.add(
                TabularColumn(
                    meta_id=meta.id,
                    name=col["name"],
                    dtype=col.get("dtype", "string"),
                    null_count=col.get("null_count", 0),
                    unique_count=col.get("unique_count", 0),
                    stats=col.get("stats"),
                )
            )

        n_rows = meta.n_rows or 0
        n_cols = meta.n_cols or 0
        total_cells = n_rows * n_cols
        total_nulls = sum(c.get("null_count", 0) for c in parsed.get("columns", []))
        null_ratio = (total_nulls / total_cells) if total_cells > 0 else 0.0

        try:
            avg_cardinality = (
                mean([c.get("unique_count", 0) for c in parsed.get("columns", [])]) if parsed.get("columns") else None
            )
        except Exception:
            avg_cardinality = None

        metrics = TabularMetrics(
            dataset_id=dataset_id,
            null_ratio=null_ratio,
            avg_cardinality=avg_cardinality,
        )
        db.session.add(metrics)

        # Si quieres disparar versionado aquí, llama a VersioningService tras commit o integra en tu flujo de subida.
        db.session.commit()

        return {
            "status": "ok",
            "dataset_id": dataset_id,
            "hubfile_id": hubfile_id,
            "file_path": file_path,
            "meta_id": meta.id,
            "n_rows": meta.n_rows,
            "n_cols": meta.n_cols,
            "null_ratio": null_ratio,
            "avg_cardinality": avg_cardinality,
        }
