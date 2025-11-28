from app.modules.flamapy.repositories import FlamapyRepository
from core.services.BaseService import BaseService


class FlamapyService(BaseService):
    def __init__(self):
        super().__init__(FlamapyRepository())

    @staticmethod
    def should_skip_file(file_name: str | None) -> bool:
        """Return True when the provided file should bypass Flamapy (e.g., CSV tabular data)."""
        return bool(file_name and file_name.lower().endswith(".csv"))
