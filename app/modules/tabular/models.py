# app/modules/tabular/models.py
from flask import request

from app import db
from app.modules.dataset.models import BaseDataset


class TabularDataset(BaseDataset):
    __mapper_args__ = {"polymorphic_identity": "tabular"}

    rows_count = db.Column(db.Integer, nullable=True)
    schema_json = db.Column(db.Text, nullable=True)

    meta_data = db.relationship(
        "TabularMetaData",
        backref="dataset",
        uselist=False,
        cascade="all, delete-orphan",
    )

    metrics = db.relationship("TabularMetrics", backref="dataset", uselist=False, cascade="all, delete-orphan")

    def validate_domain(self):
        if self.rows_count is not None and self.rows_count < 0:
            raise ValueError("rows_count cannot be negative")

    def ui_blocks(self):
        return ["common-meta", "table-schema", "sample-rows", "versioning"]

    def get_cleaned_publication_type(self):
        """Retorna el publication_type formateado"""
        if not self.ds_meta_data or not self.ds_meta_data.publication_type:
            return "Unknown"
        return self.ds_meta_data.publication_type.name.replace("_", " ").title()

    def get_uvlhub_doi(self):
        """Retorna el DOI de UVLHub"""
        from app.modules.dataset.services import DataSetService

        return DataSetService().get_uvlhub_doi(self)

    def to_dict(self):
        meta = self.meta_data
        tags = self.ds_meta_data.tags.split(",") if self.ds_meta_data and self.ds_meta_data.tags else []
        return {
            "type": "tabular",
            "dataset_type": "tabular",
            "dataset_type_label": "CSV",
            "dataset_badge_class": "bg-info",
            "title": self.ds_meta_data.title if self.ds_meta_data else "",
            "id": self.id,
            "created_at": self.created_at,
            "created_at_timestamp": int(self.created_at.timestamp()) if self.created_at else None,
            "description": self.ds_meta_data.description if self.ds_meta_data else "",
            "authors": [author.to_dict() for author in self.ds_meta_data.authors] if self.ds_meta_data else [],
            "publication_type": self.get_cleaned_publication_type(),
            "publication_doi": self.ds_meta_data.publication_doi if self.ds_meta_data else None,
            "dataset_doi": self.ds_meta_data.dataset_doi if self.ds_meta_data else None,
            "tags": tags,
            "url": self.get_uvlhub_doi(),
            "download": f"{request.host_url.rstrip('/')}/dataset/download/{self.id}",
            "zenodo": None,
            "files": [],
            "files_count": 1,
            "total_size_in_bytes": None,
            "total_size_in_human_format": None,
            "n_rows": meta.n_rows if meta else None,
            "n_cols": meta.n_cols if meta else None,
            "encoding": meta.encoding if meta else None,
            "delimiter": meta.delimiter if meta else None,
            "has_header": meta.has_header if meta is not None else None,
        }


class TabularMetaData(db.Model):
    """
    Guarda los metadatos generales del archivo CSV (la "radiografía").
    Relación 1-a-1 con TabularDataset.
    """

    __tablename__ = "tabular_meta_data"
    id = db.Column(db.Integer, primary_key=True)

    # --- Campos del checklist ---
    hubfile_id = db.Column(db.Integer)
    delimiter = db.Column(db.String(5))
    encoding = db.Column(db.String(20))
    has_header = db.Column(db.Boolean, default=True)
    n_rows = db.Column(db.Integer)
    n_cols = db.Column(db.Integer)

    # JSON para datos complejos
    primary_keys = db.Column(db.JSON)
    index_cols = db.Column(db.JSON)
    sample_rows = db.Column(db.JSON)

    dataset_id = db.Column(db.Integer, db.ForeignKey("data_set.id"), unique=True, nullable=False)

    columns = db.relationship(
        "TabularColumn",
        backref="meta_data",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )


class TabularColumn(db.Model):
    """
    Guarda los metadatos de CADA columna del CSV.
    Relación N-a-1 con TabularMetaData.
    """

    __tablename__ = "tabular_column"
    id = db.Column(db.Integer, primary_key=True)

    # --- Campos del checklist ---
    name = db.Column(db.String(255), nullable=False)
    dtype = db.Column(db.String(50))
    null_count = db.Column(db.Integer, default=0)
    unique_count = db.Column(db.Integer, default=0)
    stats = db.Column(db.JSON)

    # --- Conexión (ForeignKey) ---
    # Conexión N-a-1 con TabularMetaData
    meta_id = db.Column(db.Integer, db.ForeignKey("tabular_meta_data.id"), nullable=False)


class TabularMetrics(db.Model):
    """
    (Opcional) Guarda métricas de calidad de alto nivel.
    Relación 1-a-1 con TabularDataset.
    """

    __tablename__ = "tabular_metrics"
    id = db.Column(db.Integer, primary_key=True)

    # --- Campos del checklist ---
    null_ratio = db.Column(db.Float)
    avg_cardinality = db.Column(db.Float)

    # --- Conexión (ForeignKey) ---
    # Conexión 1-a-1 con TabularDataset
    dataset_id = db.Column(db.Integer, db.ForeignKey("data_set.id"), unique=True, nullable=False)
