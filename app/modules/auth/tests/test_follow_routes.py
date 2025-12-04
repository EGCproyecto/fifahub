import pytest

from app import db
from app.modules.auth.models import UserFollowAuthor, UserFollowCommunity
from app.modules.auth.services import AuthenticationService
from app.modules.conftest import login
from app.modules.dataset.models import Author


def _create_user_via_service(email: str, password: str = "pwd12345"):
    service = AuthenticationService()
    return service.create_with_profile(name="Test", surname="User", email=email, password=password)


def _create_author(name: str = "Route Author", author_id: int | None = None):
    author = Author(id=author_id, name=name, affiliation="Aff", orcid=None)
    db.session.add(author)
    db.session.commit()
    return author


def test_follow_author_requires_login(test_client, clean_database):
    test_client.get("/logout")
    response = test_client.post("/follow/author/1")

    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")


def test_follow_and_unfollow_author_flow(test_client, clean_database):
    with test_client.application.app_context():
        user = _create_user_via_service("follow_author@example.com")
        author = _create_author(author_id=user.id + 1)
        user_email = user.email
        author_id = author.id

    login(test_client, email=user_email, password="pwd12345")

    follow_resp = test_client.post(f"/follow/author/{author_id}")
    assert follow_resp.status_code == 200
    with test_client.application.app_context():
        assert UserFollowAuthor.query.count() == 1

    unfollow_resp = test_client.post(f"/unfollow/author/{author_id}")
    assert unfollow_resp.status_code == 200
    with test_client.application.app_context():
        assert UserFollowAuthor.query.count() == 0
    test_client.get("/logout")


def test_follow_author_not_found_returns_404(test_client, clean_database):
    with test_client.application.app_context():
        user = _create_user_via_service("missing_author@example.com")
        user_email = user.email

    login(test_client, email=user_email, password="pwd12345")

    resp = test_client.post("/follow/author/9999")

    assert resp.status_code == 404
    assert b"Author not found" in resp.data
    test_client.get("/logout")


def test_follow_and_unfollow_community_flow(test_client, clean_database):
    with test_client.application.app_context():
        user = _create_user_via_service("follow_community@example.com")
        user_email = user.email

    login(test_client, email=user_email, password="pwd12345")

    community_id = "community-xyz"
    follow_resp = test_client.post(f"/follow/community/{community_id}")
    assert follow_resp.status_code == 200
    with test_client.application.app_context():
        assert UserFollowCommunity.query.count() == 1

    unfollow_resp = test_client.post(f"/unfollow/community/{community_id}")
    assert unfollow_resp.status_code == 200
    with test_client.application.app_context():
        assert UserFollowCommunity.query.count() == 0
    test_client.get("/logout")


def test_follow_community_requires_login(test_client, clean_database):
    test_client.get("/logout")
    response = test_client.post("/follow/community/demo")

    assert response.status_code == 302
    assert "/login" in response.headers.get("Location", "")
