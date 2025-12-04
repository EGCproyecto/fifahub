from app import db
from app.modules.auth.models import User
from app.modules.auth.services import FollowService
from app.modules.dataset.models import Author, DSMetaData, PublicationType
from app.modules.dataset.services.notification_service import notification_service
from app.modules.tabular.models import TabularDataset


def _create_user(email: str) -> User:
    user = User(email=email)
    user.set_password("pwd12345")
    db.session.add(user)
    db.session.commit()
    return user


def test_author_notification_flow(monkeypatch, test_app, clean_database):
    sent_emails: list[dict] = []

    def fake_send_email(subject, recipients, html_body):
        sent_emails.append({"subject": subject, "recipients": recipients, "html_body": html_body})

    monkeypatch.setattr("core.services.email_service.send_email", fake_send_email)

    with test_app.app_context():
        follower = _create_user("follower@example.com")
        uploader = _create_user("uploader@example.com")
        author = Author(id=follower.id + 100, name="Notifier Author", affiliation="Aff")
        db.session.add(author)
        db.session.commit()

        FollowService().follow_author(follower, author)

        ds_md = DSMetaData(
            title="Dataset Notif",
            description="Desc",
            publication_type=PublicationType.OTHER,
        )
        ds_md.authors.append(author)
        db.session.add(ds_md)
        db.session.flush()

        dataset = TabularDataset(id=author.id + 1000, user_id=uploader.id, ds_meta_data_id=ds_md.id)
        db.session.add(dataset)
        db.session.commit()

        notification_service.notify_new_dataset_sync(dataset)

        assert len(sent_emails) >= 1
        assert follower.email in sent_emails[0]["recipients"]
        assert "Notifier Author" in sent_emails[0]["subject"]


def test_community_notification_flow(monkeypatch, test_app, clean_database):
    sent_emails: list[dict] = []

    def fake_send_email(subject, recipients, html_body):
        sent_emails.append({"subject": subject, "recipients": recipients, "html_body": html_body})

    monkeypatch.setattr("core.services.email_service.send_email", fake_send_email)

    with test_app.app_context():
        follower = _create_user("comm-follower@example.com")
        uploader = _create_user("comm-uploader@example.com")
        author = Author(name="Community Author", affiliation="Aff")
        db.session.add(author)
        db.session.commit()

        community_id = "community-123"
        FollowService().follow_community(follower, community_id)

        ds_md = DSMetaData(
            title="Dataset Comm",
            description="Desc",
            publication_type=PublicationType.OTHER,
            tags=f"community:{community_id}",
        )
        ds_md.authors.append(author)
        db.session.add(ds_md)
        db.session.flush()

        dataset = TabularDataset(user_id=uploader.id, ds_meta_data_id=ds_md.id)
        db.session.add(dataset)
        db.session.commit()

        notification_service.notify_new_dataset_sync(dataset)

        assert len(sent_emails) >= 1
        assert follower.email in sent_emails[0]["recipients"]
        assert community_id in sent_emails[0]["subject"]
