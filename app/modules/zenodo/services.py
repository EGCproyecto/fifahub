from __future__ import annotations

import logging
import os
import requests
from dotenv import load_dotenv
from flask import Response, jsonify
from flask_login import current_user


from app.modules.zenodo.repositories import ZenodoRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)
load_dotenv()


class ZenodoService(BaseService):
    def __init__(self):
        super().__init__(ZenodoRepository())
        self.ZENODO_ACCESS_TOKEN = self.get_zenodo_access_token()
        self.ZENODO_API_URL = self.get_zenodo_url()
        self.headers = {"Content-Type": "application/json"}
        self.params = {"access_token": self.ZENODO_ACCESS_TOKEN}

    # -------------------------------------------------------------------------
    # CONFIG Y UTILIDADES
    # -------------------------------------------------------------------------
    def get_zenodo_url(self) -> str:
        env = os.getenv("FLASK_ENV", "development")
        if env == "production":
            default_url = "https://zenodo.org/api/deposit/depositions"
        else:
            default_url = "https://sandbox.zenodo.org/api/deposit/depositions"
        return os.getenv("ZENODO_API_URL", default_url)

    def get_zenodo_access_token(self) -> str:
        return os.getenv("ZENODO_ACCESS_TOKEN")

    # -------------------------------------------------------------------------
    # TESTS DE CONEXIÓN
    # -------------------------------------------------------------------------
    def test_connection(self) -> bool:
        """Testea la conexión básica con Zenodo."""
        response = requests.get(
            self.ZENODO_API_URL, params=self.params, headers=self.headers
        )
        return response.status_code == 200

    def test_full_connection(self) -> Response:
        """
        Test completo: crear una deposition temporal, subir un archivo vacío y borrarlo.
        """
        success = True
        messages = []

        working_dir = os.getenv("WORKING_DIR", "")
        file_path = os.path.join(working_dir, "test_file.txt")

        with open(file_path, "w") as f:
            f.write("This is a test file with some content.")

        # Crear deposition
        data = {
            "metadata": {
                "title": "Test Deposition",
                "upload_type": "dataset",
                "description": "This is a test deposition created via Zenodo API",
                "creators": [{"name": "John Doe"}],
            }
        }

        response = requests.post(
            self.ZENODO_API_URL, json=data, params=self.params, headers=self.headers
        )
        if response.status_code != 201:
            return jsonify(
                {
                    "success": False,
                    "messages": f"Failed to create deposition (code {response.status_code})",
                }
            )

        deposition_id = response.json()["id"]

        # Subir archivo
        files = {"file": open(file_path, "rb")}
        upload_url = f"{self.ZENODO_API_URL}/{deposition_id}/files"
        response = requests.post(upload_url, params=self.params, files=files)
        files["file"].close()

        if response.status_code != 201:
            messages.append(f"Failed to upload file. Code: {response.status_code}")
            success = False

        # Borrar deposition
        requests.delete(f"{self.ZENODO_API_URL}/{deposition_id}", params=self.params)

        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({"success": success, "messages": messages})

    # -------------------------------------------------------------------------
    # MÉTODOS PRINCIPALES
    # -------------------------------------------------------------------------
    def get_all_depositions(self) -> dict:
        response = requests.get(
            self.ZENODO_API_URL, params=self.params, headers=self.headers
        )
        if response.status_code != 200:
            raise Exception("Failed to get depositions")
        return response.json()

    def create_new_deposition(self, dataset: "DataSet") -> dict:
        """Crea una nueva deposition en Zenodo a partir de un DataSet."""
        logger.info("Dataset sending to Zenodo...")

        metadata = {
            "title": dataset.ds_meta_data.title,
            "upload_type": (
                "dataset"
                if dataset.ds_meta_data.publication_type.value == "none"
                else "publication"
            ),
            "publication_type": (
                dataset.ds_meta_data.publication_type.value
                if dataset.ds_meta_data.publication_type.value != "none"
                else None
            ),
            "description": dataset.ds_meta_data.description,
            "creators": [
                {
                    "name": author.name,
                    **(
                        {"affiliation": author.affiliation}
                        if author.affiliation
                        else {}
                    ),
                    **({"orcid": author.orcid} if author.orcid else {}),
                }
                for author in dataset.ds_meta_data.authors
            ],
            "keywords": (
                ["uvlhub"]
                if not dataset.ds_meta_data.tags
                else dataset.ds_meta_data.tags.split(", ") + ["uvlhub"]
            ),
            "access_right": "open",
            "license": "CC-BY-4.0",
        }

        data = {"metadata": metadata}

        response = requests.post(
            self.ZENODO_API_URL, params=self.params, json=data, headers=self.headers
        )
        if response.status_code != 201:
            raise Exception(f"Failed to create deposition. Details: {response.json()}")
        return response.json()

    def upload_file(
        self,
        dataset: "DataSet",
        deposition_id: int,
        feature_model: "FeatureModel",
        user=None,
    ) -> dict:
        """Sube un archivo a una deposition existente."""
        uvl_filename = feature_model.fm_meta_data.uvl_filename
        data = {"name": uvl_filename}
        user_id = current_user.id if user is None else user.id
        file_path = os.path.join(
            uploads_folder_name(),
            f"user_{user_id}",
            f"dataset_{dataset.id}",
            uvl_filename,
        )

        files = {"file": open(file_path, "rb")}
        upload_url = f"{self.ZENODO_API_URL}/{deposition_id}/files"
        response = requests.post(upload_url, params=self.params, data=data, files=files)
        files["file"].close()

        if response.status_code != 201:
            raise Exception(f"Failed to upload file. Details: {response.json()}")
        return response.json()

    def publish_deposition(self, deposition_id: int) -> dict:
        """Publica una deposition existente en Zenodo."""
        publish_url = f"{self.ZENODO_API_URL}/{deposition_id}/actions/publish"
        response = requests.post(publish_url, params=self.params, headers=self.headers)
        if response.status_code != 202:
            raise Exception("Failed to publish deposition")
        return response.json()

    def get_deposition(self, deposition_id: int) -> dict:
        """Obtiene los datos de una deposition concreta."""
        dep_url = f"{self.ZENODO_API_URL}/{deposition_id}"
        response = requests.get(dep_url, params=self.params, headers=self.headers)
        if response.status_code != 200:
            raise Exception("Failed to get deposition")
        return response.json()

    def get_doi(self, deposition_id: int) -> str:
        """Obtiene el DOI de una deposition."""
        return self.get_deposition(deposition_id).get("doi")
