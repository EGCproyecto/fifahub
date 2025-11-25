import os
from unittest.mock import MagicMock, patch

import pytest

from app import create_app, db
from app.modules.fakenodo.repositories import FakenodoRepository
from app.modules.fakenodo.services import FakenodoService

# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture(autouse=True)
def mock_db_session(monkeypatch):
    """Prevent real DB writes."""
    monkeypatch.setattr(db.session, "add", MagicMock())
    monkeypatch.setattr(db.session, "commit", MagicMock())
    monkeypatch.setattr(db.session, "delete", MagicMock())


@pytest.fixture
def app():
    """Create a Flask app for context use in tests."""
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        yield app


@pytest.fixture
def repository():
    return FakenodoRepository()


@pytest.fixture
def service():
    srv = FakenodoService()
    srv.repository = MagicMock()
    return srv


@pytest.fixture
def mock_dataset():
    mock = MagicMock()
    mock.id = 1
    mock.ds_meta_data.title = "Unit Dataset"
    mock.ds_meta_data.description = "Dataset for testing"
    mock.ds_meta_data.authors = []
    mock.ds_meta_data.tags = "csv, test"
    mock.ds_meta_data.publication_type.value = "none"
    return mock


@pytest.fixture
def mock_feature_model():
    mock = MagicMock()
    mock.fm_meta_data.csv_filename = "dataset.csv"
    return mock


# ============================================================
# REPOSITORY TESTS
# ============================================================


def test_repo_create_and_get(repository, app):
    with app.app_context():
        dep = MagicMock()
        dep.id = 1
        dep.meta_data = {"title": "Repo Test"}
        repository.create_new_deposition = MagicMock(return_value=dep)
        repository.get_deposition = MagicMock(return_value=dep)
        got = repository.get_deposition(dep.id)
        assert got.meta_data["title"] == "Repo Test"


def test_repo_delete(repository, app):
    with app.app_context():
        dep = MagicMock()
        dep.id = 1
        repository.create_new_deposition = MagicMock(return_value=dep)
        repository.delete_deposition = MagicMock(return_value=True)
        assert repository.delete_deposition(dep.id) is True


def test_repo_add_csv_file(repository, tmp_path, app):
    with app.app_context():
        dep = MagicMock()
        dep.id = 1
        dep.files = []
        repository.create_new_deposition = MagicMock(return_value=dep)
        repository.add_csv_file = MagicMock()
        csv_path = tmp_path / "file.csv"
        csv_path.write_text("id,name,value\n1,John,123")
        repository.add_csv_file(dep.id, "file.csv", str(csv_path))
        repository.add_csv_file.assert_called_once()


# ============================================================
# SERVICE TESTS
# ============================================================


def test_service_create_new_deposition(service, mock_dataset, app):
    with app.app_context():
        fake_dep = MagicMock()
        fake_dep.id = 1
        fake_dep.meta_data = {"title": "X"}
        service.repository.create_new_deposition.return_value = fake_dep
        result = service.create_new_deposition(mock_dataset)
        assert result["deposition_id"] == 1
        assert "doi" in result


def test_service_create_invalid_dataset(service):
    invalid = MagicMock()
    invalid.ds_meta_data = None
    with pytest.raises(Exception):
        service.create_new_deposition(invalid)


def test_service_upload_file_creates_csv(service, mock_dataset, mock_feature_model, tmp_path):
    """Should create a new CSV file if it does not already exist."""
    mock_dep = MagicMock()
    mock_dep.id = 42  # unique deposition
    service.repository.get_deposition.return_value = mock_dep
    service.repository.add_csv_file = MagicMock()

    # Force unique dataset ID
    mock_dataset.id = 99

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True)
    patch_user = patch("app.modules.fakenodo.services.current_user", MagicMock(id=77))
    patch_path = patch(
        "core.configuration.configuration.uploads_folder_name",
        return_value=str(upload_dir),
    )

    file_path = upload_dir / "user_77" / "dataset_99" / "dataset.csv"
    if file_path.exists():
        os.remove(file_path)

    with patch_user, patch_path:
        res = service.upload_file(mock_dataset, 42, mock_feature_model)

    assert "file_metadata" in res
    assert res["message"].startswith("The CSV")
    assert os.path.exists(file_path)


def test_service_upload_file_already_exists(service, mock_dataset, mock_feature_model, tmp_path):
    mock_dep = MagicMock()
    mock_dep.id = 1
    service.repository.get_deposition.return_value = mock_dep

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True)
    os.makedirs(upload_dir / "user_1" / "dataset_1", exist_ok=True)
    file_path = upload_dir / "user_1" / "dataset_1" / "dataset.csv"
    file_path.write_text("existing data")

    patch_user = patch("app.modules.fakenodo.services.current_user", MagicMock(id=1))
    patch_path = patch(
        "core.configuration.configuration.uploads_folder_name",
        return_value=str(upload_dir),
    )

    with patch_user, patch_path:
        res = service.upload_file(mock_dataset, 1, mock_feature_model)

    assert res["status"] == "conflict"


def test_service_publish_deposition_success(service, tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("id,name,value\n1,Alice,123")

    mock_dep = MagicMock()
    mock_dep.id = 1
    mock_dep.files = [{"file_name": "data.csv", "file_path": str(csv_path)}]
    mock_dep.meta_data = {}
    mock_dep.status = "draft"
    service.repository.get_deposition.return_value = mock_dep

    res = service.publish_deposition(1)
    assert res["status"] == "published"
    assert "csv_files_info" in res
    assert res["csv_files_info"][0]["file_name"] == "data.csv"


def test_service_publish_deposition_no_files(service):
    mock_dep = MagicMock()
    mock_dep.id = 1
    mock_dep.files = []
    service.repository.get_deposition.return_value = mock_dep

    res = service.publish_deposition(1)
    assert res["status"] == "draft"
    assert "No CSV files" in res["message"]


def test_service_get_deposition(service):
    fake_dep = MagicMock()
    fake_dep.id = 1
    fake_dep.meta_data = {"title": "Demo"}
    service.repository.get_deposition.return_value = fake_dep
    result = service.get_deposition(1)
    assert result.meta_data["title"] == "Demo"


def test_service_get_doi_new(service):
    fake_dep = MagicMock()
    fake_dep.id = 1
    fake_dep.doi = None
    service.repository.get_deposition.return_value = fake_dep

    doi = service.get_doi(1)

    assert doi == "10.5281/fakenodo.1"
    assert fake_dep.doi == "10.5281/fakenodo.1"


def test_service_get_doi_existing(service):
    fake_dep = MagicMock()
    fake_dep.doi = "10.5281/fakenodo.9"
    service.repository.get_deposition.return_value = fake_dep
    assert service.get_doi(1) == "10.5281/fakenodo.9"


def test_service_delete_deposition_removes_files(service, tmp_path):
    fake_file = tmp_path / "to_delete.csv"
    fake_file.write_text("dummy data")

    mock_dep = MagicMock()
    mock_dep.id = 1
    mock_dep.files = [{"file_path": str(fake_file)}]
    service.repository.get_deposition.return_value = mock_dep
    service.repository.delete_deposition.return_value = True

    res = service.delete_deposition(1)
    assert "deleted successfully" in res["message"]
    assert not os.path.exists(fake_file)


def test_service_delete_deposition_not_found(service):
    service.repository.get_deposition.side_effect = Exception("Deposition not found.")
    with pytest.raises(Exception):
        service.delete_deposition(404)
