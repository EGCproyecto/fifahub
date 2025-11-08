import csv
import hashlib
import logging
import os

from dotenv import load_dotenv
from flask_login import current_user

from app.modules.dataset.models import DataSet
from app.modules.fakenodo.repositories import FakenodoRepository
from app.modules.featuremodel.models import FeatureModel
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)
load_dotenv()


class FakenodoService(BaseService):
    """
    Local service that emulates Zenodo for CSV datasets.
    Manages creation, upload, publication, retrieval, and deletion of fake depositions.
    """

    def __init__(self):
        self.repository = FakenodoRepository()

    # -------------------------------------------------------------
    # Retrieve all depositions
    # -------------------------------------------------------------
    def get_all_depositions(self) -> dict:
        """Return all simulated depositions."""
        return self.repository.storage

    # -------------------------------------------------------------
    # Create a new deposition
    # -------------------------------------------------------------
    def create_new_deposition(
        self, dataset: DataSet, publication_doi: str = None
    ) -> dict:
        """Create a new deposition in Fakenodo."""
        deposition_id = dataset.id
        fake_doi = (
            f"{publication_doi}/dataset{deposition_id}"
            if publication_doi
            else f"10.5281/fakenodo.{deposition_id}"
        )

        metadata = self._build_metadata(dataset)
        fakenodo = self.repository.create_new_fakenodo(meta_data=metadata, doi=fake_doi)

        # Store locally as well
        logger.info(f"Fakenodo created in memory: {fake_doi}")
        return self._build_response(
            fakenodo, metadata, "Fakenodo created successfully.", fake_doi
        )

    # -------------------------------------------------------------
    # Upload CSV file
    # -------------------------------------------------------------
    def upload_file(
        self,
        dataset: DataSet,
        deposition_id: int,
        feature_model: FeatureModel,
        user=None,
    ) -> dict:
        """Simulate uploading a CSV file to Fakenodo."""
        fakenodo = self.repository.storage.get(deposition_id)
        if not fakenodo:
            raise Exception(f"Deposition {deposition_id} not found.")

        file_name = getattr(feature_model.fm_meta_data, "csv_filename", "dataset.csv")
        user_id = current_user.id if user is None else user.id

        file_path = os.path.join(
            uploads_folder_name(),
            f"user_{user_id}",
            f"dataset_{dataset.id}",
            file_name,
        )

        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w") as f:
                f.write("id,name,value\n1,example,123\n2,another,456\n3,final,789\n")

            self.repository.add_csv_file(deposition_id, file_name, file_path)
            logger.info(f"CSV uploaded: {file_name}")

            return {
                "message": f"The CSV '{file_name}' was uploaded successfully.",
                "file_metadata": {
                    "file_name": file_name,
                    "file_size": os.path.getsize(file_path),
                    "file_type": "text/csv",
                    "file_url": f"/uploads/user_{user_id}/dataset_{dataset.id}/{file_name}",
                },
            }

        logger.warning(f"CSV file '{file_name}' already exists in storage.")
        return {
            "message": "File already exists.",
            "status": "conflict",
            "file": file_name,
        }

    # -------------------------------------------------------------
    # Publish deposition
    # -------------------------------------------------------------
    def publish_deposition(self, fakenodo_id: int) -> dict:
        """Simulate publishing a deposition by reading its CSVs."""
        fakenodo = self.repository.storage.get(fakenodo_id)
        if not fakenodo:
            raise Exception(f"Fakenodo {fakenodo_id} not found.")

        if not fakenodo["files"]:
            return {
                "id": fakenodo_id,
                "status": "draft",
                "message": "No CSV files found.",
            }

        csv_summaries = []
        for file_info in fakenodo["files"]:
            file_path = file_info["file_path"]
            file_name = file_info["file_name"]

            with open(file_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                rows = list(reader)
                num_rows = len(rows)
                num_cols = len(rows[0]) if num_rows > 0 else 0

            checksum = self._calculate_checksum(file_path)
            csv_summaries.append(
                {
                    "file_name": file_name,
                    "rows": num_rows,
                    "columns": num_cols,
                    "checksum": checksum,
                    "size_bytes": os.path.getsize(file_path),
                }
            )

        fakenodo["doi"] = f"10.5281/fakenodo.{fakenodo_id}.v{len(fakenodo['files'])}"
        fakenodo["status"] = "published"
        logger.info(f"Fakenodo published: {fakenodo['doi']}")

        return {
            "id": fakenodo_id,
            "status": "published",
            "conceptdoi": fakenodo["doi"],
            "message": "Fakenodo published successfully.",
            "csv_files_info": csv_summaries,
        }

    # -------------------------------------------------------------
    # Retrieve, DOI and Delete
    # -------------------------------------------------------------
    def get_deposition(self, fakenodo_id: int) -> dict:
        fakenodo = self.repository.storage.get(fakenodo_id)
        if not fakenodo:
            raise Exception(f"Fakenodo {fakenodo_id} not found.")
        return fakenodo

    def get_doi(self, fakenodo_id: int) -> str:
        fakenodo = self.repository.storage.get(fakenodo_id)
        if not fakenodo:
            raise Exception(f"Fakenodo {fakenodo_id} not found.")
        if not fakenodo.get("doi"):
            fakenodo["doi"] = self._generate_doi(fakenodo_id)
        return fakenodo["doi"]

    def delete_deposition(self, fakenodo_id: int) -> dict:
        fakenodo = self.repository.storage.get(fakenodo_id)
        if not fakenodo:
            raise Exception(f"Fakenodo {fakenodo_id} not found.")

        for file_info in fakenodo.get("files", []):
            file_path = file_info.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    logger.warning("Could not delete file at %s", file_path)

        if self.repository.delete_fakenodo(fakenodo_id):
            logger.info(f"Fakenodo deleted: {fakenodo_id}")
            return {"message": f"Fakenodo {fakenodo_id} deleted successfully."}

        raise Exception(f"Fakenodo {fakenodo_id} not found.")
    # -------------------------------------------------------------
    # Helper methods
    # -------------------------------------------------------------
    def _build_metadata(self, dataset: DataSet) -> dict:
        ds = dataset.ds_meta_data
        return {
            "title": ds.title,
            "upload_type": (
                "dataset" if ds.publication_type.value == "none" else "publication"
            ),
            "description": ds.description,
            "file_type": "text/csv",
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
                for author in ds.authors
            ],
            "keywords": (
                ["fakenodo", "csv"]
                if not ds.tags
                else ds.tags.split(", ") + ["fakenodo", "csv"]
            ),
            "access_right": "open",
            "license": "CC-BY-4.0",
        }

    def _build_response(self, fakenodo, meta_data, message, doi) -> dict:
        return {
            "deposition_id": fakenodo["id"],
            "doi": doi,
            "meta_data": meta_data,
            "message": message,
        }

    def _calculate_checksum(self, file_path: str) -> str:
        with open(file_path, "rb") as file:
            return hashlib.sha256(file.read()).hexdigest()

    def _generate_doi(self, fakenodo_id: int) -> str:
        return f"10.5281/fakenodo.{fakenodo_id}"
