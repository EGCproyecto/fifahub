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


def _create_tabular_dataset(owner: User, title: str = "Dataset Detail"):
    md = DSMetaData(title=title, description="Desc", publication_type=PublicationType.OTHER)
    db.session.add(md)
    db.session.flush()
    ds = TabularDataset(user_id=owner.id, ds_meta_data_id=md.id)
    db.session.add(ds)
    db.session.commit()
    return ds


def test_other_user_can_view_dataset_detail(test_client, clean_database):
    with test_client.application.app_context():
        owner = _create_user("downer@example.com")
        other = _create_user("dviewer@example.com")
        dataset = _create_tabular_dataset(owner)
        dataset_id = dataset.id

    login(test_client, email="dviewer@example.com", password="pwd12345")
    resp = test_client.get(f"/dataset/view/{dataset_id}")
    assert resp.status_code == 200
    assert b"Dataset Detail" in resp.data
