import csv
import hashlib
import logging
import os

from dotenv import load_dotenv
from flask_login import current_user

import core.configuration.configuration as config
from app.modules.dataset.models import DataSet
from app.modules.fakenodo.repositories import FakenodoRepository
from app.modules.featuremodel.models import FeatureModel
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)
load_dotenv()


class FakenodoService(BaseService):
    """
    Local service that emulates Zenodo for CSV datasets.
    Manages creation, upload, publication, retrieval, and deletion of depositions.
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
    def create_new_deposition(self, dataset: DataSet, publication_doi: str = None) -> dict:
        """Create a new deposition in Fakenodo."""
        deposition_id = dataset.id
        fake_doi = (
            f"{publication_doi}/dataset{deposition_id}" if publication_doi else f"10.5281/fakenodo.{deposition_id}"
        )

        # Inline metadata creation
        ds = dataset.ds_meta_data
        metadata = {
            "title": ds.title,
            "upload_type": "dataset" if ds.publication_type.value == "none" else "publication",
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

        deposition = self.repository.create_new_deposition(meta_data=metadata, doi=fake_doi)
        logger.info(f"FakenodoService: Created deposition {fake_doi}")

        # Inline response building
        return {
            "deposition_id": deposition.id,
            "doi": fake_doi,
            "meta_data": metadata,
            "message": "Deposition created successfully.",
        }

    # -------------------------------------------------------------
    # Upload CSV to deposition
    # -------------------------------------------------------------
    def upload_file(
        self,
        dataset: DataSet,
        deposition_id: int,
        feature_model: FeatureModel = None,
        user=None,
    ) -> dict:
        """Simulate uploading a CSV file to a deposition."""
        deposition = self.repository.get_deposition(deposition_id)
        if not deposition:
            raise Exception(f"Deposition {deposition_id} not found.")

        # Determine filename
        if feature_model is not None and hasattr(feature_model, "fm_meta_data"):
            file_name = getattr(feature_model.fm_meta_data, "csv_filename", "dataset.csv")
        else:
            file_name = "dataset.csv"

        user_id = current_user.id if user is None else user.id
        file_path = os.path.join(
            config.uploads_folder_name(),
            f"user_{user_id}",
            f"dataset_{dataset.id}",
            file_name,
        )

        # Check for file existence
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("id,name,value\n1,example,123\n2,another,456\n3,final,789\n")

            self.repository.add_csv_file(deposition_id, file_name, file_path)
            logger.info(f"FakenodoService: CSV uploaded '{file_name}'")

            return {
                "message": f"The CSV '{file_name}' was uploaded successfully.",
                "file_metadata": {
                    "file_name": file_name,
                    "file_size": os.path.getsize(file_path),
                    "file_type": "text/csv",
                    "file_url": f"/uploads/user_{user_id}/dataset_{dataset.id}/{file_name}",
                },
            }

        logger.warning(f"CSV file '{file_name}' already exists for deposition {deposition_id}")
        return {
            "message": "File already exists.",
            "status": "conflict",
            "file": file_name,
        }

    # -------------------------------------------------------------
    # Publish a deposition
    # -------------------------------------------------------------
    def publish_deposition(self, deposition_id: int) -> dict:
        """Simulate publishing a deposition by reading its CSVs."""
        deposition = self.repository.get_deposition(deposition_id)
        if not deposition:
            raise Exception(f"Deposition {deposition_id} not found.")

        files = getattr(deposition, "files", [])
        if not files:
            return {
                "id": deposition_id,
                "status": "draft",
                "message": "No CSV files found.",
            }

        csv_summaries = []
        for file_info in files:
            file_path = file_info["file_path"]
            file_name = file_info["file_name"]

            with open(file_path, newline="", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                rows = list(reader)
                num_rows = len(rows)
                num_cols = len(rows[0]) if num_rows > 0 else 0

            # Inline checksum calculation
            with open(file_path, "rb") as file:
                checksum = hashlib.sha256(file.read()).hexdigest()

            csv_summaries.append(
                {
                    "file_name": file_name,
                    "rows": num_rows,
                    "columns": num_cols,
                    "checksum": checksum,
                    "size_bytes": os.path.getsize(file_path),
                }
            )

        deposition.doi = f"10.5281/fakenodo.{deposition_id}.v{len(files)}"
        deposition.status = "published"
        logger.info(f"FakenodoService: Published deposition {deposition.doi}")

        return {
            "id": deposition_id,
            "status": "published",
            "conceptdoi": deposition.doi,
            "message": "Deposition published successfully.",
            "csv_files_info": csv_summaries,
        }

    # -------------------------------------------------------------
    # Get deposition
    # -------------------------------------------------------------
    def get_deposition(self, deposition_id: int):
        deposition = self.repository.get_deposition(deposition_id)
        return deposition if deposition else None

    # -------------------------------------------------------------
    # Get DOI
    # -------------------------------------------------------------
    def get_doi(self, deposition_id: int) -> str:
        deposition = self.repository.get_deposition(deposition_id)
        if not deposition:
            raise Exception(f"Deposition {deposition_id} not found.")
        if not deposition.doi:
            # Inline DOI generation
            deposition.doi = f"10.5281/fakenodo.{deposition_id}"
        return deposition.doi

    # -------------------------------------------------------------
    # Delete deposition
    # -------------------------------------------------------------
    def delete_deposition(self, deposition_id: int) -> dict:
        deposition = self.repository.get_deposition(deposition_id)
        if not deposition:
            raise Exception(f"Deposition {deposition_id} not found.")

        for file_info in getattr(deposition, "files", []):
            file_path = file_info.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    logger.warning("Could not delete file at %s", file_path)

        if self.repository.delete_deposition(deposition_id):
            logger.info(f"FakenodoService: Deleted deposition {deposition_id}")
            return {"message": f"Deposition {deposition_id} deleted successfully."}

        raise Exception(f"Deposition {deposition_id} not found.")
