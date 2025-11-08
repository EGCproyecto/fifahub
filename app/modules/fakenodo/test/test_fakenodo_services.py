import csv
import os
from types import SimpleNamespace

import pytest

import app.modules.fakenodo.services as fakenodo_services
from app.modules.fakenodo.services import FakenodoService

# -----------------------------
# Dummies para DataSet y FeatureModel
# -----------------------------


class DummyAuthor:
    def __init__(self, name, affiliation=None, orcid=None):
        self.name = name
        self.affiliation = affiliation
        self.orcid = orcid


class DummyPublicationType:
    def __init__(self, value: str):
        self.value = value


class DummyDSMetaData:
    def __init__(
        self,
        title="Test dataset",
        description="Desc",
        tags="tag1, tag2",
        publication_type_value="none",
        authors=None,
    ):
        self.title = title
        self.description = description
        self.tags = tags
        self.publication_type = DummyPublicationType(publication_type_value)
        self.authors = authors or [DummyAuthor("Author One")]


class DummyDataSet:
    def __init__(self, ds_id: int = 1, ds_meta: DummyDSMetaData | None = None):
        self.id = ds_id
        self.ds_meta_data = ds_meta or DummyDSMetaData()


class DummyFMMetaData:
    def __init__(self, csv_filename="dataset.csv"):
        self.csv_filename = csv_filename


class DummyFeatureModel:
    def __init__(self, csv_filename="dataset.csv"):
        self.fm_meta_data = DummyFMMetaData(csv_filename)


# -----------------------------
# Fixture de entorno para el servicio
# -----------------------------


@pytest.fixture
def service(tmp_path, monkeypatch) -> FakenodoService:

    monkeypatch.setattr(
        fakenodo_services,
        "uploads_folder_name",
        lambda: str(tmp_path),
        raising=False,
    )

    # current_user simulado (cuando user=None en upload_file)
    fake_user = SimpleNamespace(id=42)
    monkeypatch.setattr(
        fakenodo_services,
        "current_user",
        fake_user,
        raising=False,
    )

    return FakenodoService()


# ============================================================
# Tests de create_new_deposition()
# ============================================================


def test_create_new_deposition_generates_default_doi_and_stores_metadata(
    service: FakenodoService,
):
    dataset = DummyDataSet(ds_id=1)
    resp = service.create_new_deposition(dataset)

    # DOI por defecto
    assert resp["doi"] == "10.5281/fakenodo.1"

    dep_id = resp["deposition_id"]
    assert dep_id in service.repository.storage

    stored = service.repository.storage[dep_id]
    assert stored["status"] == "draft"
    assert stored["meta_data"]["title"] == dataset.ds_meta_data.title
    assert "fakenodo" in stored["meta_data"]["keywords"]
    assert "csv" in stored["meta_data"]["keywords"]
    assert stored["meta_data"]["upload_type"] == "dataset"


def test_create_new_deposition_uses_publication_doi_when_provided(
    service: FakenodoService,
):
    dataset = DummyDataSet(ds_id=2)
    pub_doi = "10.9999/publication"
    resp = service.create_new_deposition(dataset, publication_doi=pub_doi)

    assert resp["doi"] == "10.9999/publication/dataset2"


# ============================================================
# Tests de upload_file()
# ============================================================


def test_upload_file_creates_csv_and_registers_in_repository(
    service: FakenodoService, tmp_path
):
    dataset = DummyDataSet(ds_id=3)
    feature_model = DummyFeatureModel(csv_filename="mydata.csv")

    # Primero creamos la deposición
    resp = service.create_new_deposition(dataset)
    dep_id = resp["deposition_id"]

    result = service.upload_file(dataset, dep_id, feature_model)

    # Mensaje de éxito
    assert "uploaded successfully" in result["message"]

    # Fichero existe donde debe
    expected_path = tmp_path / "user_42" / "dataset_3" / "mydata.csv"
    assert expected_path.exists()

    # Contenido CSV (cabecera + 3 filas)
    with expected_path.open(encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert rows[0] == ["id", "name", "value"]
    assert len(rows) == 4  # 1 header + 3 rows

    # El repo tiene registrado el fichero
    stored = service.repository.storage[dep_id]
    assert len(stored["files"]) == 1
    assert stored["files"][0]["file_name"] == "mydata.csv"


def test_upload_file_when_file_exists_returns_conflict(
    service: FakenodoService, tmp_path
):
    dataset = DummyDataSet(ds_id=4)
    feature_model = DummyFeatureModel(csv_filename="duplicate.csv")

    resp = service.create_new_deposition(dataset)
    dep_id = resp["deposition_id"]

    # Primera subida -> éxito
    service.upload_file(dataset, dep_id, feature_model)

    # Segunda subida -> conflicto
    result = service.upload_file(dataset, dep_id, feature_model)

    assert result["status"] == "conflict"
    assert result["file"] == "duplicate.csv"

    stored = service.repository.storage[dep_id]
    assert len(stored["files"]) == 1  # no se duplica


# ============================================================
# Tests de publish_deposition()
# ============================================================


def test_publish_deposition_without_files_returns_draft_status(
    service: FakenodoService,
):
    dataset = DummyDataSet(ds_id=5)
    resp = service.create_new_deposition(dataset)
    dep_id = resp["deposition_id"]

    result = service.publish_deposition(dep_id)

    assert result["status"] == "draft"
    assert "No CSV files found" in result["message"]


def test_publish_deposition_reads_csv_and_sets_doi_and_status(
    service: FakenodoService, tmp_path
):
    dataset = DummyDataSet(ds_id=6)
    feature1 = DummyFeatureModel(csv_filename="file1.csv")
    feature2 = DummyFeatureModel(csv_filename="file2.csv")

    resp = service.create_new_deposition(dataset)
    dep_id = resp["deposition_id"]

    # Subimos dos CSV
    service.upload_file(dataset, dep_id, feature1)
    service.upload_file(dataset, dep_id, feature2)

    result = service.publish_deposition(dep_id)

    assert result["status"] == "published"
    assert len(result["csv_files_info"]) == 2

    conceptdoi = result["conceptdoi"]
    assert conceptdoi.startswith("10.5281/fakenodo.")
    assert conceptdoi.endswith(".v2")  # 2 ficheros -> versión 2

    # Comprobamos resumen de un fichero
    info = result["csv_files_info"][0]
    assert info["rows"] == 4  # 1 header + 3 filas
    assert info["columns"] == 3  # id, name, value
    assert info["size_bytes"] > 0
    assert "checksum" in info


# ============================================================
# Tests de delete_deposition()
# ============================================================


def test_delete_deposition_removes_from_repository_and_deletes_csv(
    service: FakenodoService, tmp_path
):
    dataset = DummyDataSet(ds_id=7)
    feature_model = DummyFeatureModel(csv_filename="todelete.csv")

    resp = service.create_new_deposition(dataset)
    dep_id = resp["deposition_id"]

    upload_result = service.upload_file(dataset, dep_id, feature_model)
    file_url = upload_result["file_metadata"]["file_url"]

    # Ruta absoluta del fichero en disco
    expected_path = tmp_path / "user_42" / "dataset_7" / "todelete.csv"
    assert expected_path.exists()

    result = service.delete_deposition(dep_id)

    assert "deleted successfully" in result["message"]
    assert dep_id not in service.repository.storage

    assert not expected_path.exists()
