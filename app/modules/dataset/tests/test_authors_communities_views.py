from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import Author, DataSet, DSMetaData, PublicationType


def _create_user(email: str) -> User:
    user = User(email=email)
    user.set_password("pwd12345")
    db.session.add(user)
    db.session.commit()
    return user


def _create_dataset_with_author(user: User, author: Author, doi: str | None = None, community: str | None = None):
    md = DSMetaData(
        title="Test Dataset",
        description="Desc",
        publication_type=PublicationType.OTHER,
        dataset_doi=doi,
        tags=f"community:{community}" if community else None,
    )
    md.authors.append(author)
    db.session.add(md)
    db.session.flush()
    ds = DataSet(user_id=user.id, ds_meta_data_id=md.id)
    db.session.add(ds)
    db.session.commit()
    return ds


def test_authors_list_view(test_client, clean_database):
    with test_client.application.app_context():
        user = _create_user("authorlist@example.com")
        author = Author(id=5001, name="List Author")
        db.session.add(author)
        db.session.commit()
        _create_dataset_with_author(user, author, doi="10.1234/list-author")

    resp = test_client.get("/datasets/authors")
    assert resp.status_code == 200
    assert b"List Author" in resp.data


def test_communities_list_view(test_client, clean_database):
    with test_client.application.app_context():
        user = _create_user("communitylist@example.com")
        author = Author(id=5002, name="Comm Author")
        db.session.add(author)
        db.session.commit()
        _create_dataset_with_author(user, author, doi="10.1234/comm-author", community="comm-x")

    resp = test_client.get("/datasets/communities")
    assert resp.status_code == 200
    assert b"comm-x" in resp.data


def test_author_and_community_detail_views(test_client, clean_database):
    with test_client.application.app_context():
        user = _create_user("detail@example.com")
        author = Author(id=6001, name="Detail Author")
        db.session.add(author)
        db.session.commit()
        _create_dataset_with_author(user, author, doi="10.1234/detail", community="detail-comm")

    author_resp = test_client.get(f"/authors/{author.id}")
    assert author_resp.status_code == 200
    assert b"Detail Author" in author_resp.data

    community_resp = test_client.get("/communities/detail-comm")
    assert community_resp.status_code == 200
    assert b"detail-comm" in community_resp.data
