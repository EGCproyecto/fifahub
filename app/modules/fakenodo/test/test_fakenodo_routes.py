import pytest
from types import SimpleNamespace

from app import create_app
from app.modules.fakenodo import routes as fakenodo_routes


@pytest.fixture
def client(monkeypatch):
    app = create_app()
    app.testing = True

    class FakeFakenodoService:
        def __init__(self):
            self.called = SimpleNamespace(
                create=False,
                upload=False,
                publish=False,
                delete=False,
            )
            self.last_args = {}

        def create_new_deposition(self, dataset, publication_doi=None):
            self.called.create = True
            self.last_args["create"] = {"dataset": dataset, "publication_doi": publication_doi}
            return {
                "deposition_id": 1,
                "doi": "10.5281/fakenodo.1",
                "meta_data": {"title": "Test dataset"},
                "message": "Fakenodo created successfully.",
            }

        def upload_file(self, dataset, deposition_id, feature_model, user=None):
            self.called.upload = True
            self.last_args["upload"] = {
                "dataset": dataset,
                "deposition_id": deposition_id,
                "feature_model": feature_model,
                "user": user,
            }
            return {
                "message": "The CSV 'dataset.csv' was uploaded successfully.",
                "file_metadata": {
                    "file_name": "dataset.csv",
                    "file_size": 123,
                    "file_type": "text/csv",
                    "file_url": "/uploads/user_1/dataset_1/dataset.csv",
                },
            }

        def publish_deposition(self, fakenodo_id: int):
            self.called.publish = True
            self.last_args["publish"] = {"fakenodo_id": fakenodo_id}
            return {
                "id": fakenodo_id,
                "status": "published",
                "conceptdoi": f"10.5281/fakenodo.{fakenodo_id}.v1",
                "message": "Fakenodo published successfully.",
                "csv_files_info": [],
            }

        def delete_deposition(self, fakenodo_id: int):
            self.called.delete = True
            self.last_args["delete"] = {"fakenodo_id": fakenodo_id}
            return {"message": f"Fakenodo {fakenodo_id} deleted successfully."}

    fake_service = FakeFakenodoService()

    monkeypatch.setattr(
        fakenodo_routes,
        "fakenodo_service",
        fake_service,
        raising=False,
    )

    with app.test_client() as test_client:
        login_resp = test_client.post(
            "/login",
            data={"email": "user1@example.com", "password": "1234"},
            follow_redirects=True,
        )
        # Opcional: asegurar que el login ha ido bien
        assert login_resp.status_code in (200, 302)

        yield test_client, fake_service

        

def test_create_deposition_endpoint_calls_service_and_returns_201(client):
    test_client, fake_service = client

    response = test_client.post(
        "/fakenodo/depositions",
        json={"dataset_id": 1, "publication_doi": None},
    )

    assert response.status_code in (200, 201)
    data = response.get_json()

    assert data["deposition_id"] == 1
    assert data["doi"] == "10.5281/fakenodo.1"
    assert fake_service.called.create is True


def test_upload_file_endpoint_calls_service_and_returns_metadata(client):
    test_client, fake_service = client

    response = test_client.post(
        "/fakenodo/depositions/1/upload",
        json={"dataset_id": 1, "feature_model_id": 1},
    )

    assert response.status_code == 200
    data = response.get_json()

    assert "file_metadata" in data
    assert data["file_metadata"]["file_name"] == "dataset.csv"
    assert fake_service.called.upload is True
    assert fake_service.last_args["upload"]["deposition_id"] == 1


def test_publish_deposition_endpoint_calls_service_and_returns_published_status(client):
    test_client, fake_service = client

    response = test_client.post("/fakenodo/depositions/1/publish")

    assert response.status_code == 200
    data = response.get_json()

    assert data["status"] == "published"
    assert data["conceptdoi"] == "10.5281/fakenodo.1.v1"
    assert fake_service.called.publish is True
    assert fake_service.last_args["publish"]["fakenodo_id"] == 1


def test_delete_deposition_endpoint_calls_service_and_returns_message(client):
    test_client, fake_service = client

    response = test_client.delete("/fakenodo/depositions/1")

    assert response.status_code == 200
    data = response.get_json()

    assert "deleted successfully" in data["message"]
    assert fake_service.called.delete is True
    assert fake_service.last_args["delete"]["fakenodo_id"] == 1
