import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import DSMetaData, PublicationType, UVLDataset
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


def _create_dataset_record(user, title: str, download_count: int):
    metadata = DSMetaData(title=title, description="Desc", publication_type=PublicationType.BOOK)
    db.session.add(metadata)
    db.session.flush()
    dataset = UVLDataset(user_id=user.id, ds_meta_data_id=metadata.id, download_count=download_count)
    db.session.add(dataset)
    db.session.commit()
    return dataset


@pytest.mark.usefixtures("clean_database")
def test_trending_endpoint_limits_and_sorts(test_app, test_client):
    with test_app.app_context():
        user = User(email="trending@test.local")
        user.set_password("secret")
        db.session.add(user)
        db.session.commit()

        counts = [2, 7, 1, 9, 3, 5]
        for idx, count in enumerate(counts):
            _create_dataset_record(user, title=f"Dataset {idx}", download_count=count)

    resp = test_client.get("/datasets/trending")
    assert resp.status_code == 200

    payload = resp.get_json()
    assert len(payload) == 5  # limited to top 5
    returned_counts = [item["download_count"] for item in payload]
    assert returned_counts == sorted(returned_counts, reverse=True)
    assert max(counts) == returned_counts[0]
    assert min(counts) not in returned_counts  # lowest one dropped by the limit


@pytest.mark.usefixtures("clean_database")
def test_trending_endpoint_reflects_latest_downloads(test_app, test_client):
    with test_app.app_context():
        user = User(email="refresh@test.local")
        user.set_password("secret")
        db.session.add(user)
        db.session.commit()

        top = _create_dataset_record(user, title="Top dataset", download_count=3)
        rising = _create_dataset_record(user, title="Rising dataset", download_count=1)

    first = test_client.get("/datasets/trending")
    assert first.status_code == 200
    before = {item["title"]: item["download_count"] for item in first.get_json()}
    assert before["Top dataset"] == 3
    assert before["Rising dataset"] == 1

    with test_app.app_context():
        to_update = UVLDataset.query.get(rising.id)
        to_update.download_count = 6
        db.session.commit()

    refreshed = test_client.get("/datasets/trending")
    assert refreshed.status_code == 200
    after = refreshed.get_json()
    after_map = {item["title"]: item["download_count"] for item in after}

    assert after_map["Rising dataset"] == 6
    assert after[0]["title"] == "Rising dataset"
    assert after_map["Rising dataset"] > before["Rising dataset"]


if __name__ == "__main__":
    unittest.main()
