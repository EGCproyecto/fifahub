# app/modules/dataset/services/versioning_service.py
from typing import Optional

from app import db
from app.modules.dataset.models import DatasetVersion

from .versioning_strategies import TabularVersionStrategy, UVLVersionStrategy


class VersioningService:
    def __init__(self, tabular=None, uvl=None):
        self.tabular_strategy = tabular or TabularVersionStrategy()
        self.uvl_strategy = uvl or UVLVersionStrategy()

    def _next_version(self, dataset) -> str:
        last = DatasetVersion.query.filter_by(dataset_id=dataset.id).order_by(DatasetVersion.created_at.desc()).first()
        if not last:
            return "1.0.0"
        major, minor, patch = (int(x) for x in last.version.split("."))
        patch += 1
        return f"{major}.{minor}.{patch}"

    def create_version(
        self, dataset, author_id=None, change_note: Optional[str] = None, strategy: Optional[str] = None
    ):
        # Heurística por extensiones si no se fuerza
        if strategy == "tabular":
            strat = self.tabular_strategy
        elif strategy == "uvl":
            strat = self.uvl_strategy
        else:
            has_csv = any(f.name.lower().endswith(".csv") for fm in dataset.feature_models for f in fm.files)
            has_uvl = any(f.name.lower().endswith(".uvl") for fm in dataset.feature_models for f in fm.files)
            strat = self.tabular_strategy if has_csv and not has_uvl else self.uvl_strategy

        snapshot = strat.snapshot(dataset)
        version = self._next_version(dataset)

        dv = DatasetVersion(
            dataset_id=dataset.id,
            version=version,
            author_id=author_id,
            change_note=change_note,
            metadata=snapshot,
        )
        db.session.add(dv)
        db.session.commit()
        return dv
