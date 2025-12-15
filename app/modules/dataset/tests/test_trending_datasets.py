import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.modules.dataset.services.services import DataSetService


class TestTrendingDatasets(unittest.TestCase):
    def setUp(self):
        self.service = DataSetService()
        # monkeypatch repository with mocks
        self.service.repository = MagicMock()

    def _make_ds(self, ds_id, downloads):
        return SimpleNamespace(id=ds_id, download_count=downloads)

    def test_recent_results_are_sorted_desc(self):
        recent = [self._make_ds(1, 5), self._make_ds(2, 10), self._make_ds(3, 7)]
        self.service.repository.trending_recent.return_value = recent

        result = self.service.get_trending_datasets()

        downloads = [ds.download_count for ds in result]
        self.assertEqual(downloads, sorted(downloads, reverse=True))
        # fallback should not be called when recent exists
        self.service.repository.top_downloaded.assert_not_called()

    def test_fallback_sorted_desc_when_no_recent(self):
        self.service.repository.trending_recent.return_value = []
        fallback = [self._make_ds(1, 3), self._make_ds(2, 9), self._make_ds(3, 1)]
        self.service.repository.top_downloaded.return_value = fallback

        result = self.service.get_trending_datasets()

        downloads = [ds.download_count for ds in result]
        self.assertEqual(downloads, sorted(downloads, reverse=True))
        self.service.repository.top_downloaded.assert_called_once()


if __name__ == "__main__":
    unittest.main()
