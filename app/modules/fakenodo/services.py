import hashlib
import logging
import os
import csv

from dotenv import load_dotenv
from flask_login import current_user

from app.modules.dataset.models import DataSet, DSMetaData
from app.modules.featuremodel.models import FeatureModel
from app.modules.fakenodo.models import Fakenodo
from app.modules.fakenodo.repositories import FakenodoRepository
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)
load_dotenv()


class FakenodoService(BaseService):
    """
    Local service that emulates Zenodo.
    Allows creation, upload, publishing, retrieval, and deletion of CSV-based depositions.
    """

    def __init__(self):
        self.fakenodo_repository = FakenodoRepository()
        self.fakenodos = {}  # Dictionary used as an in-memory database for depositions.

    # -------------------------------------------------------------
    # Retrieve all depositions
    # -------------------------------------------------------------
    def get_all_depositions(self) -> dict:
        """
        Return all simulated depositions stored in Fakenodo.
        """
        return self.fakenodos

    # -------------------------------------------------------------
    # Create a new deposition
    # -------------------------------------------------------------
    def create_new_deposition(self, dataset: DataSet, publication_doi: str = None) -> dict:
        """
        Create a new deposition in Fakenodo.

        Args:
            dataset (DataSet): Dataset containing the metadata.
            publication_doi (str): Optional previous DOI.

        Returns:
            dict: Information about the created deposition.
        """
        deposition_id = dataset.id
        fake_doi = (
            f"{publication_doi}/dataset{deposition_id}" if publication_doi else f"10.5281/fakenodo.{deposition_id}"
        )

        metadata = self._build_metadata(dataset)

        # Attempt to create the deposition using the repository
        fakenodo = self.fakenodo_repository.create_new_fakenodo(meta_data=metadata)

        # Validate creation result (simulate Zenodo’s API behavior)
        if fakenodo and isinstance(fakenodo, Fakenodo):
            self.fakenodos[deposition_id] = {
                "id": deposition_id,
                "metadata": metadata,
                "files": [],
                "doi": fake_doi,
                "status": "draft",
            }
            logger.info(f"Fakenodo created locally: {fake_doi}")

            return self._build_response(
                fakenodo,
                metadata,
                "Fakenodo successfully created.",
                fake_doi,
            )
        else:
            error_message = "Failed to create Fakenodo: repository returned an invalid object."
            logger.error(error_message)
            raise Exception(error_message)

    # -------------------------------------------------------------
    # Upload CSV file
    # -------------------------------------------------------------
    def upload_file(self, dataset: DataSet, deposition_id: int, feature_model: FeatureModel, user=None) -> dict:
        """
        Simulate uploading a CSV file to a deposition in Fakenodo.

        Args:
            dataset (DataSet): The dataset associated with the deposition.
            deposition_id (int): The deposition ID.
            feature_model (FeatureModel): The feature model object.
            user (User): The owner of the uploaded file.

        Returns:
            dict: JSON-style response with upload details.
        """
        if deposition_id not in self.fakenodos:
            error_message = f"Deposition {deposition_id} not found."
            logger.error(error_message)
            raise Exception(error_message)

        file_name = getattr(feature_model.fm_meta_data, "csv_filename", "dataset.csv")
        user_id = current_user.id if user is None else user.id

        file_path = os.path.join(
            uploads_folder_name(),
            f"user_{user_id}",
            f"dataset_{dataset.id}",
            file_name,
        )

        # Simulate CSV file upload
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Create a mock CSV file
            with open(file_path, "w") as f:
                f.write("id,name,value\n1,example,123\n2,another,456\n3,final,789\n")

            # Register file in memory
            self.fakenodos[deposition_id]["files"].append(file_name)
            logger.info(f"CSV file uploaded: {file_name}")

            file_metadata = {
                "file_name": file_name,
                "file_size": os.path.getsize(file_path),
                "file_type": "text/csv",
                "file_url": f"/uploads/user_{user_id}/dataset_{dataset.id}/{file_name}",
            }

            return {
                "message": f"The CSV '{file_name}' was uploaded successfully to Fakenodo.",
                "file_metadata": file_metadata,
            }

        else:
            # Simulate “409 Conflict” if the file already exists
            error_message = f"The CSV file '{file_name}' already exists in Fakenodo storage."
            logger.warning(error_message)

            return {
                "message": error_message,
                "status": "conflict",
                "file": file_name,
            }

    # -------------------------------------------------------------
    # Publish CSV deposition
    # -------------------------------------------------------------
    def publish_deposition(self, fakenodo_id: int) -> dict:
        """
        Simulate publishing a deposition and reading all associated CSV files.

        Args:
            fakenodo_id (int): The deposition ID.

        Returns:
            dict: Information about the published deposition, including CSV summaries.
        """
        fakenodo = self.fakenodos.get(fakenodo_id)
        if not fakenodo:
            error_message = f"Fakenodo with ID {fakenodo_id} not found."
            logger.error(error_message)
            raise Exception(error_message)

        if not fakenodo["files"]:
            error_message = f"No CSV files found for Fakenodo {fakenodo_id}."
            logger.warning(error_message)
            return {
                "id": fakenodo_id,
                "status": "draft",
                "message": error_message,
            }

        csv_summaries = []

        # Read CSV files and extract simple metadata
        for file_name in fakenodo["files"]:
            if file_name.endswith(".csv"):
                for root, dirs, files in os.walk("uploads"):
                    if file_name in files:
                        file_path = os.path.join(root, file_name)
                        with open(file_path, newline="", encoding="utf-8") as csvfile:
                            reader = csv.reader(csvfile)
                            rows = list(reader)
                            num_rows = len(rows)
                            num_cols = len(rows[0]) if num_rows > 0 else 0

                        csv_summaries.append(
                            {
                                "file_name": file_name,
                                "path": file_path,
                                "rows": num_rows,
                                "columns": num_cols,
                                "size_bytes": os.path.getsize(file_path),
                            }
                        )

        if not csv_summaries:
            error_message = f"No valid CSV files found for Fakenodo {fakenodo_id}."
            logger.warning(error_message)
            return {
                "id": fakenodo_id,
                "status": "draft",
                "message": error_message,
            }

        fakenodo["doi"] = f"10.5281/fakenodo.{fakenodo_id}.v{len(fakenodo['files'])}"
        fakenodo["status"] = "published"

        logger.info(f"Fakenodo published successfully: {fakenodo['doi']}")

        return {
            "id": fakenodo_id,
            "status": "published",
            "conceptdoi": fakenodo["doi"],
            "message": "Fakenodo published successfully. CSV files processed.",
            "csv_files_info": csv_summaries,
        }

    # -------------------------------------------------------------
    # Retrieve, DOI and Delete operations
    # -------------------------------------------------------------
    def get_deposition(self, fakenodo_id: int) -> dict:
        """
        Retrieve a local deposition and show associated CSV files if present.
        """
        fakenodo = self.fakenodos.get(fakenodo_id)
        if not fakenodo:
            raise Exception(f"Fakenodo {fakenodo_id} not found.")
        return fakenodo

    def get_doi(self, fakenodo_id: int) -> str:
        """
        Return the DOI associated with the fakenodo.
        """
        fakenodo = self.fakenodos.get(fakenodo_id)
        if not fakenodo:
            raise Exception(f"Fakenodo {fakenodo_id} not found.")

        if "doi" not in fakenodo or not fakenodo["doi"]:
            fakenodo["doi"] = self._generate_doi(fakenodo_id)

        return fakenodo["doi"]

    def delete_deposition(self, fakenodo_id: int) -> dict:
        """
        Delete a simulated deposition and remove associated CSV files from local storage.
        """
        if fakenodo_id not in self.fakenodos:
            raise Exception("Deposition not found.")

        fakenodo = self.fakenodos[fakenodo_id]
        deleted_files = []

        for file_name in fakenodo.get("files", []):
            if file_name.endswith(".csv"):
                for root, dirs, files in os.walk("uploads"):
                    if file_name in files:
                        file_path = os.path.join(root, file_name)
                        try:
                            os.remove(file_path)
                            deleted_files.append(file_name)
                        except Exception as e:
                            logger.warning(f"Could not delete file {file_name}: {str(e)}")

        del self.fakenodos[fakenodo_id]
        logger.info(f"Fakenodo deleted: {fakenodo_id}")

        return {"message": "Deposition deleted successfully.", "deleted_csv_files": deleted_files}

    # -------------------------------------------------------------
    # Internal helper methods
    # -------------------------------------------------------------
    def _build_metadata(self, dataset: DataSet) -> dict:
        """
        Build metadata from a dataset (CSV-oriented).
        """
        ds = dataset.ds_meta_data
        return {
            "title": ds.title,
            "upload_type": "dataset" if ds.publication_type.value == "none" else "publication",
            "publication_type": None if ds.publication_type.value == "none" else ds.publication_type.value,
            "description": ds.description,
            "file_type": "text/csv",
            "creators": [
                {
                    "name": author.name,
                    **({"affiliation": author.affiliation} if author.affiliation else {}),
                    **({"orcid": author.orcid} if author.orcid else {}),
                }
                for author in ds.authors
            ],
            "keywords": (["fakenodo", "csv"] if not ds.tags else ds.tags.split(", ") + ["fakenodo", "csv"]),
            "access_right": "open",
            "license": "CC-BY-4.0",
        }

    def _build_response(self, fakenodo, meta_data, message, doi) -> dict:
        """
        Create a standardized JSON-like response.
        """
        return {
            "deposition_id": fakenodo["id"],
            "doi": doi,
            "meta_data": meta_data,
            "message": message,
        }

    def _calculate_checksum(self, file_path: str) -> str:
        """
        Calculate the SHA-256 checksum of a CSV file.
        """
        with open(file_path, "rb") as file:
            return hashlib.sha256(file.read()).hexdigest()

    def _generate_doi(self, fakenodo_id: int) -> str:
        """
        Generate a fake DOI for a CSV deposition.
        """
        return f"10.5281/fakenodo.{fakenodo_id}"
