import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class FakenodoRepository:
    """In-memory repository to simulate Zenodo deposit storage."""

    def __init__(self):
        # Simulated "database" (key: fakenodo_id, value: fakenodo_data)
        self.storage: Dict[int, Dict[str, Any]] = {}
        self.counter = 1  # Simulates auto-increment IDs

    def create_new_fakenodo(self, meta_data: dict = None, doi: str = None) -> dict:
        """
        Create a new Fakenodo entry in memory.

        Args:
            meta_data (dict): Metadata for the Fakenodo (title, description, etc.).
            doi (str): Optional DOI string.

        Returns:
            dict: The newly created Fakenodo record.
        """
        if meta_data is None:
            meta_data = {}

        fakenodo_id = self.counter
        self.counter += 1

        fakenodo_entry = {
            "id": fakenodo_id,
            "meta_data": meta_data,
            "doi": doi,
            "files": [],  # Here we'll store uploaded CSV file info
            "status": "draft",
        }

        # Store it in memory
        self.storage[fakenodo_id] = fakenodo_entry

        logger.info(f"FakenodoRepository: Created new Fakenodo with ID {fakenodo_id}")
        return fakenodo_entry

    def add_csv_file(self, fakenodo_id: int, file_name: str, file_path: str) -> dict:
        """
        Attach a CSV file to an existing Fakenodo record.

        Args:
            fakenodo_id (int): The Fakenodo ID.
            file_name (str): The CSV filename.
            file_path (str): The simulated local path.

        Returns:
            dict: File metadata added to the Fakenodo.
        """
        if fakenodo_id not in self.storage:
            raise Exception(f"Fakenodo with ID {fakenodo_id} not found.")

        file_info = {
            "file_name": file_name,
            "file_path": file_path,
            "file_type": "text/csv",
        }

        self.storage[fakenodo_id]["files"].append(file_info)

        logger.info(
            f"FakenodoRepository: Added CSV file '{file_name}' to Fakenodo ID {fakenodo_id}"
        )
        return file_info

    def get_fakenodo(self, fakenodo_id: int) -> dict:
        """
        Get a Fakenodo by ID.
        """
        fakenodo = self.storage.get(fakenodo_id)
        if not fakenodo:
            raise Exception(f"Fakenodo with ID {fakenodo_id} not found.")
        return fakenodo

    def delete_fakenodo(self, fakenodo_id: int) -> bool:
        """
        Delete a Fakenodo entry from memory.

        Args:
            fakenodo_id (int): The ID of the Fakenodo to delete.

        Returns:
            bool: True if deleted, False otherwise.
        """
        if fakenodo_id in self.storage:
            del self.storage[fakenodo_id]
            logger.info(f"FakenodoRepository: Deleted Fakenodo with ID {fakenodo_id}")
            return True

        logger.warning(
            f"FakenodoRepository: Tried to delete non-existent ID {fakenodo_id}"
        )
        return False
