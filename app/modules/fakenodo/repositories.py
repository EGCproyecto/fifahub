import logging

from app import db
from app.modules.fakenodo.models import Fakenodo

logger = logging.getLogger(__name__)


class FakenodoRepository:
    """Repository for interacting with the Fakenodo depositions in the database."""

    def create_new_deposition(self, meta_data: dict = None, doi: str = None) -> Fakenodo:
        """
        Create a new deposition entry in the database.

        Args:
            meta_data (dict): Metadata for the deposition (title, description, etc.)
            doi (str): Optional DOI string.

        Returns:
            Fakenodo: The newly created database object.
        """
        if meta_data is None:

            meta_data = {}
        # Testing hooks here dont mind this message
        deposition = Fakenodo(meta_data=meta_data, doi=doi)
        db.session.add(deposition)
        db.session.commit()

        logger.info(f"FakenodoRepository: Created new deposition with ID {deposition.id}")
        return deposition

    def add_csv_file(self, deposition_id: int, file_name: str, file_path: str) -> dict:
        """
        Attach a CSV file to an existing deposition record.

        Args:
            deposition_id (int): The deposition ID.
            file_name (str): The CSV filename.
            file_path (str): The simulated local path.

        Returns:
            dict: Updated meta_data with file information.
        """
        deposition = Fakenodo.query.get(deposition_id)
        if not deposition:
            raise Exception(f"Deposition with ID {deposition_id} not found.")

        # Add CSV info inside meta_data["files"]
        meta_data = deposition.meta_data or {}
        files = meta_data.get("files", [])
        files.append(
            {
                "file_name": file_name,
                "file_path": file_path,
                "file_type": "text/csv",
            }
        )
        meta_data["files"] = files
        deposition.meta_data = meta_data

        db.session.commit()

        logger.info(f"FakenodoRepository: Added CSV file '{file_name}' to deposition ID {deposition_id}")
        return meta_data

    def get_deposition(self, deposition_id: int) -> Fakenodo:
        """
        Retrieve a deposition entry by its ID.

        Args:
            deposition_id (int): The ID of the deposition.

        Returns:
            Fakenodo: The corresponding database object.
        """
        deposition = Fakenodo.query.get(deposition_id)
        if not deposition:
            raise Exception(f"Deposition with ID {deposition_id} not found.")
        return deposition

    def delete_deposition(self, deposition_id: int) -> bool:
        """
        Delete a deposition entry from the database.

        Args:
            deposition_id (int): The ID of the deposition to delete.

        Returns:
            bool: True if deleted, False otherwise.
        """
        deposition = Fakenodo.query.get(deposition_id)
        if deposition:
            db.session.delete(deposition)
            db.session.commit()
            logger.info(f"FakenodoRepository: Deleted deposition with ID {deposition_id}")
            return True

        logger.warning(f"FakenodoRepository: Tried to delete non-existent deposition ID {deposition_id}")
        return False
