import logging
import threading
from typing import Iterable

from flask import current_app, url_for

from app.modules.auth.services import FollowService
from app.modules.dataset.models import DataSet
from app.modules.dataset.services.notification_utils import (
    get_dataset_community_id,
    get_dataset_primary_author,
)
from core.services import email_service

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, follow_service: FollowService | None = None):
        self.follow_service = follow_service or FollowService()

    import threading

import logging

from flask import current_app

from app.modules.dataset.models import DataSet

logger = logging.getLogger(__name__)


class NotificationService:
    ...

    def trigger_new_dataset_notifications_async(self, dataset):
        dataset_id = getattr(dataset, "id", None)
        if not dataset_id:
            return

        app = current_app._get_current_object()

        def _worker(dataset_id=dataset_id, app=app):
            try:
                with app.app_context():
                    ds = DataSet.query.get(dataset_id)
                    if ds is not None:
                        self.notify_new_dataset_sync(ds)
            except Exception:
                logger.exception("Error in notification worker for dataset_id=%s", dataset_id)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def notify_new_dataset_sync(self, dataset: DataSet) -> None:
        try:
            self._notify_author_followers(dataset)
        except Exception:
            logger.exception("Author notification failed for dataset_id=%s", getattr(dataset, "id", None))

        try:
            self._notify_community_followers(dataset)
        except Exception:
            logger.exception("Community notification failed for dataset_id=%s", getattr(dataset, "id", None))

    def _notify_author_followers(self, dataset: DataSet) -> None:
        author = get_dataset_primary_author(dataset)
        if not author:
            return

        followers = self.follow_service.get_followers_for_author(author) or []
        if not followers:
            return

        subject = f"[fifahub] New dataset from {author.name}"
        dataset_url = self._dataset_url(dataset)
        description = getattr(getattr(dataset, "ds_meta_data", None), "description", "") or ""
        html_body = (
            f"<p>You are receiving this email because you follow this author.</p>"
            f"<p><strong>{author.name}</strong> published a new dataset:</p>"
            f"<p><strong>{self._dataset_title(dataset)}</strong></p>"
            f"<p>{description}</p>"
            f'<p><a href="{dataset_url}">View dataset</a></p>'
        )

        self._send_to_users(followers, subject, html_body)

    def _notify_community_followers(self, dataset: DataSet) -> None:
        community_id = get_dataset_community_id(dataset)
        if not community_id:
            return

        followers = self.follow_service.get_followers_for_community(community_id) or []
        if not followers:
            return

        subject = f"[fifahub] New dataset in community {community_id}"
        dataset_url = self._dataset_url(dataset)
        description = getattr(getattr(dataset, "ds_meta_data", None), "description", "") or ""
        html_body = (
            f"<p>You are receiving this email because you follow this community.</p>"
            f"<p>New dataset in <strong>{community_id}</strong>:</p>"
            f"<p><strong>{self._dataset_title(dataset)}</strong></p>"
            f"<p>{description}</p>"
            f'<p><a href="{dataset_url}">View dataset</a></p>'
        )

        self._send_to_users(followers, subject, html_body)

    def _send_to_users(self, users: Iterable, subject: str, html_body: str) -> None:
        emails = [getattr(u, "email", None) for u in users if getattr(u, "email", None)]
        if not emails:
            return
        email_service.send_email(subject=subject, recipients=emails, html_body=html_body)

    @staticmethod
    def _dataset_title(dataset: DataSet) -> str:
        try:
            return getattr(getattr(dataset, "ds_meta_data", None), "title", None) or f"Dataset {dataset.id}"
        except Exception:
            return f"Dataset {getattr(dataset, 'id', '')}"

    @staticmethod
    def _dataset_url(dataset: DataSet) -> str:
        try:
            metadata = getattr(dataset, "ds_meta_data", None)
            doi = getattr(metadata, "dataset_doi", None) if metadata else None
            if doi:
                return url_for("dataset.subdomain_index", doi=doi, _external=True)
        except Exception:
            pass
        return url_for("dataset.get_unsynchronized_dataset", dataset_id=dataset.id, _external=True)


notification_service = NotificationService()
