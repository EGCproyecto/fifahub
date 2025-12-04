from app import db
from app.modules.auth.models import User
from app.modules.conftest import login
from app.modules.dataset.models import DSMetaData, PublicationType
from app.modules.tabular.models import TabularDataset


def _create_user(email: str) -> User:
    user = User(email=email)
    user.set_password("pwd12345")
    db.session.add(user)
    db.session.commit()
    return user


def _create_tabular(user: User, title: str):
    md = DSMetaData(title=title, description="Desc", publication_type=PublicationType.OTHER)
    db.session.add(md)
    db.session.flush()
    ds = TabularDataset(user_id=user.id, ds_meta_data_id=md.id)
    db.session.add(ds)
    db.session.commit()
    return ds


def test_tabular_dataset_shown_in_explore(test_client, clean_database):
    with test_client.application.app_context():
        user = _create_user("explore@example.com")
        _create_tabular(user, title="Juan")

    login(test_client, email="explore@example.com", password="pwd12345")
    resp = test_client.get("/explore", query_string={"q": "Juan"})
    assert resp.status_code == 200
    assert b"Juan" in resp.data
