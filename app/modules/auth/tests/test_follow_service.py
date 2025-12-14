import pytest

from app import db
from app.modules.auth.models import User, UserFollowAuthor, UserFollowCommunity
from app.modules.auth.services import FollowService
from app.modules.dataset.models import Author


def _create_user(email: str) -> User:
    user = User(email=email)
    user.set_password("pwd12345")
    db.session.add(user)
    db.session.commit()
    return user


def _create_author(name: str, author_id: int | None = None) -> Author:
    author = Author(id=author_id, name=name, affiliation="Test", orcid=None)
    db.session.add(author)
    db.session.commit()
    return author


def test_follow_author_creates_record(test_app, clean_database):
    with test_app.app_context():
        user = _create_user("user1@example.com")
        author = _create_author("Author One", author_id=user.id + 1)

        follow = FollowService().follow_author(user, author)

        assert follow.user_id == user.id
        assert follow.author_id == author.id
        assert UserFollowAuthor.query.count() == 1


def test_follow_author_idempotent(test_app, clean_database):
    with test_app.app_context():
        user = _create_user("user2@example.com")
        author = _create_author("Author Two", author_id=user.id + 1)
        service = FollowService()

        first = service.follow_author(user, author)
        second = service.follow_author(user, author)

        assert first.id == second.id
        assert UserFollowAuthor.query.count() == 1


def test_unfollow_author_removes_record(test_app, clean_database):
    with test_app.app_context():
        user = _create_user("user3@example.com")
        author = _create_author("Author Three", author_id=user.id + 1)
        service = FollowService()
        service.follow_author(user, author)

        removed = service.unfollow_author(user, author)

        assert removed is True
        assert UserFollowAuthor.query.count() == 0


def test_unfollow_author_not_followed_returns_false(test_app, clean_database):
    with test_app.app_context():
        user = _create_user("user4@example.com")
        author = _create_author("Author Four", author_id=user.id + 1)

        removed = FollowService().unfollow_author(user, author)

        assert removed is False
        assert UserFollowAuthor.query.count() == 0


def test_follow_community_creates_record(test_app, clean_database):
    with test_app.app_context():
        user = _create_user("user5@example.com")
        service = FollowService()

        follow = service.follow_community(user, "community-1")

        assert follow.user_id == user.id
        assert follow.community_id == "community-1"
        assert UserFollowCommunity.query.count() == 1


def test_follow_community_idempotent(test_app, clean_database):
    with test_app.app_context():
        user = _create_user("user6@example.com")
        service = FollowService()

        first = service.follow_community(user, "community-2")
        second = service.follow_community(user, "community-2")

        assert first.id == second.id
        assert UserFollowCommunity.query.count() == 1


def test_unfollow_community_removes_record(test_app, clean_database):
    with test_app.app_context():
        user = _create_user("user7@example.com")
        service = FollowService()
        service.follow_community(user, "community-3")

        removed = service.unfollow_community(user, "community-3")

        assert removed is True
        assert UserFollowCommunity.query.count() == 0


def test_unfollow_community_not_followed_returns_false(test_app, clean_database):
    with test_app.app_context():
        user = _create_user("user8@example.com")

        removed = FollowService().unfollow_community(user, "community-4")

        assert removed is False
        assert UserFollowCommunity.query.count() == 0


def test_follow_author_cannot_follow_self(test_app, clean_database):
    with test_app.app_context():
        user = _create_user("user9@example.com")
        author = _create_author("Same Id", author_id=user.id)

        with pytest.raises(ValueError):
            FollowService().follow_author(user, author)


def test_get_followed_authors_for_user(test_app, clean_database):
    with test_app.app_context():
        user = _create_user("user10@example.com")
        author1 = _create_author("Author Ten A", author_id=user.id + 1)
        author2 = _create_author("Author Ten B", author_id=user.id + 2)
        service = FollowService()
        service.follow_author(user, author1)
        service.follow_author(user, author2)

        followed = service.get_followed_authors_for_user(user)

        assert {a.id for a in followed} == {author1.id, author2.id}


def test_get_followers_for_author(test_app, clean_database):
    with test_app.app_context():
        author = _create_author("Author Eleven", author_id=9999)
        user1 = _create_user("user11@example.com")
        user2 = _create_user("user12@example.com")
        service = FollowService()
        service.follow_author(user1, author)
        service.follow_author(user2, author)

        followers = service.get_followers_for_author(author)

        assert {u.id for u in followers} == {user1.id, user2.id}


def test_get_followed_communities_for_user(test_app, clean_database):
    with test_app.app_context():
        user = _create_user("community-list@example.com")
        service = FollowService()
        service.follow_community(user, "community-alpha")
        service.follow_community(user, "community-beta")

        followed = service.get_followed_communities_for_user(user)

        assert set(followed) == {"community-alpha", "community-beta"}


def test_get_followers_for_community(test_app, clean_database):
    with test_app.app_context():
        community_id = "community-followers"
        user1 = _create_user("community-f1@example.com")
        user2 = _create_user("community-f2@example.com")
        service = FollowService()
        service.follow_community(user1, community_id)
        service.follow_community(user2, community_id)

        followers = service.get_followers_for_community(community_id)

        assert {u.id for u in followers} == {user1.id, user2.id}


def test_follow_community_accepts_object_identifier(test_app, clean_database):
    class DummyCommunity:
        def __init__(self, identifier):
            self.name = identifier

    with test_app.app_context():
        user = _create_user("community-object@example.com")
        service = FollowService()
        follow = service.follow_community(user, DummyCommunity("obj-community"))
        assert follow.community_id == "obj-community"


def test_follow_community_requires_identifier(test_app, clean_database):
    class InvalidCommunity:
        pass

    with test_app.app_context():
        user = _create_user("community-error@example.com")
        service = FollowService()
        with pytest.raises(ValueError):
            service.follow_community(user, InvalidCommunity())


def test_follow_author_requires_persisted_user(test_app, clean_database):
    with test_app.app_context():
        user = User(email="transient@example.com")
        author = _create_author("Transient Author", author_id=9998)
        with pytest.raises(ValueError):
            FollowService().follow_author(user, author)


def test_follow_author_requires_persisted_author(test_app, clean_database):
    with test_app.app_context():
        user = _create_user("persisted@example.com")
        author = Author(name="NoID", affiliation="Aff", orcid=None)
        with pytest.raises(ValueError):
            FollowService().follow_author(user, author)


def test_follow_community_accepts_object_with_id_property(test_app, clean_database):
    class CommunityObj:
        def __init__(self, identifier):
            self.id = identifier

    with test_app.app_context():
        user = _create_user("community-id@example.com")
        service = FollowService()
        follow = service.follow_community(user, CommunityObj("community-id-123"))
        assert follow.community_id == "community-id-123"


def test_get_followers_for_community_empty(test_app, clean_database):
    with test_app.app_context():
        followers = FollowService().get_followers_for_community("non-existent")
        assert followers == []
