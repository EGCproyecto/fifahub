from app import db
from app.modules.dataset.models import DatasetVersion

from .versioning_strategies import TabularVersionStrategy, UVLVersionStrategy


class VersioningService:
    """Servicio de versionado de datasets (tabular/UVL)."""

    def __init__(self):
        self.tabular_strategy = TabularVersionStrategy()
        self.uvl_strategy = UVLVersionStrategy()

    def _next_version(self, dataset):
        """Genera el siguiente número de versión semántico (1.0.0, 1.0.1, etc.)."""
        last = DatasetVersion.query.filter_by(dataset_id=dataset.id).order_by(DatasetVersion.created_at.desc()).first()
        if not last:
            return "1.0.0"
        try:
            major, minor, patch = map(int, last.version.split("."))
            patch += 1
            return f"{major}.{minor}.{patch}"
        except ValueError:
            # fallback si el formato no es semántico
            return f"{last.version}-1"

    def create_version(self, dataset, author_id=None, change_note=None, strategy=None):
        """Crea una nueva versión del dataset según la estrategia definida."""
        # Detección automática
        if strategy == "tabular":
            strat = self.tabular_strategy
        elif strategy == "uvl":
            strat = self.uvl_strategy
        else:
            # heurística: si tiene CSV => tabular, si no => UVL
            has_csv = any(f.name.lower().endswith(".csv") for fm in dataset.feature_models for f in fm.files)
            strat = self.tabular_strategy if has_csv else self.uvl_strategy

        snapshot = strat.snapshot(dataset)
        version = self._next_version(dataset)

        dv = DatasetVersion(
            dataset_id=dataset.id,
            version=version,
            author_id=author_id,
            change_note=change_note,
            snapshot=snapshot,
        )
        db.session.add(dv)
        db.session.commit()
        return dv
