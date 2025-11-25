import shutil
from pathlib import Path

import pytest

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import BaseDataset, DSMetaData, PublicationType, UVLDataset
from app.modules.dataset.services.services import DSDownloadRecordService


def _create_dataset(user):
    metadata = DSMetaData(
        title="Dataset",
        description="Desc",
        publication_type=PublicationType.BOOK,
    )
    db.session.add(metadata)
    db.session.flush()

    dataset = UVLDataset(user_id=user.id, ds_meta_data_id=metadata.id)
    db.session.add(dataset)
    db.session.commit()
    return dataset


def test_record_download_increments_counter(test_app, clean_database):
    with test_app.app_context():
        user = User(email="unit@test.local")
        user.set_password("secret")
        db.session.add(user)
        db.session.commit()

        dataset = _create_dataset(user)

        svc = DSDownloadRecordService()
        svc.record_download(dataset, user_cookie="cookie-1", user_id=user.id)
        svc.record_download(dataset, user_cookie="cookie-2", user_id=user.id)

        refreshed = BaseDataset.query.get(dataset.id)
        assert refreshed.download_count == 2


@pytest.mark.usefixtures("clean_database")
def test_download_endpoint_updates_stats(test_app, test_client):
    uploads_root = Path("uploads")

    with test_app.app_context():
        user = User(email="client@test.local")
        user.set_password("client")
        db.session.add(user)
        db.session.commit()

        dataset = _create_dataset(user)
        dataset_dir = uploads_root / f"user_{user.id}" / f"dataset_{dataset.id}"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        (dataset_dir / "dummy.txt").write_text("content", encoding="utf-8")

    try:
        resp = test_client.get(f"/dataset/download/{dataset.id}")
        assert resp.status_code == 200

        stats = test_client.get(f"/datasets/{dataset.id}/stats").get_json()
        assert stats["downloads"] == 1

        resp = test_client.get(f"/dataset/download/{dataset.id}")
        assert resp.status_code == 200

        stats = test_client.get(f"/datasets/{dataset.id}/stats").get_json()
        assert stats["downloads"] == 2

        detail = test_client.get(f"/api/datasets/{dataset.id}").get_json()
        assert detail["download_count"] == 2
    finally:
        shutil.rmtree(uploads_root, ignore_errors=True)
