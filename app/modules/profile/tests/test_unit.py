import pytest

from app import db
from app.modules.auth.models import User
from app.modules.conftest import login

# --- ¡¡IMPORTANTE!! ---
# CAMBIA 'NOMBRE_DE_TU_ARCHIVO' por el nombre real del archivo
# donde está 'TabularDataset'. (ej. 'models_tabular', 'tabular', etc.)
from app.modules.dataset.models import BaseDataset, DSMetaData, UVLDataset
from app.modules.profile.models import UserProfile
from app.modules.tabular.models import TabularDataset


@pytest.fixture(scope="module")  # <--- Usamos "module" (rápido)
def db_setup_for_module(test_client):
    """
    Crea la BD UNA VEZ para todas las pruebas de este archivo.
    Limpia al principio y al final.
    """
    with test_client.application.app_context():
        # Limpieza inicial agresiva (por si algo quedó colgado)
        db.session.close()
        db.drop_all()
        db.engine.dispose()

        # Creamos las tablas
        db.create_all()

        # --- Creamos los datos de prueba ---
        user_viewer = User(email="user@example.com", password="test1234")
        db.session.add(user_viewer)
        db.session.commit()

        profile = UserProfile(user_id=user_viewer.id, name="Name", surname="Surname")
        db.session.add(profile)

        user_with_data = User(email="target.with.data@example.com", password="password")
        db.session.add(user_with_data)
        db.session.commit()

        meta1 = DSMetaData(title="Mi Dataset UVL", description="Desc UVL", publication_type="OTHER")
        db.session.add(meta1)
        db.session.commit()
        uvl_ds = UVLDataset(user_id=user_with_data.id, ds_meta_data_id=meta1.id)
        db.session.add(uvl_ds)

        meta2 = DSMetaData(title="Mi Dataset Tabular", description="Desc Tabular", publication_type="REPORT")
        db.session.add(meta2)
        db.session.commit()
        tab_ds = TabularDataset(user_id=user_with_data.id, ds_meta_data_id=meta2.id)
        db.session.add(tab_ds)

        user_empty = User(email="target.empty@example.com", password="password")
        db.session.add(user_empty)

        db.session.commit()

    # --- Las pruebas se ejecutan AHORA ---
    yield test_client


# =================================================================
# --- PRUEBAS ESENCIALES ---
# =================================================================


def test_edit_profile_page_get(db_setup_for_module):
    """
    (Tu prueba original) Prueba el acceso a editar perfil.
    """
    test_client = db_setup_for_module
    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200

    response = test_client.get("/profile/edit")
    assert response.status_code == 200
    assert b"Edit profile" in response.data
    # ¡¡NO HAY LOGOUT()!!


def test_view_user_datasets_page_success(db_setup_for_module):
    """
    Prueba que la página HTML de la lista de datasets se carga.
    """
    test_client = db_setup_for_module

    with test_client.application.app_context():
        target_user = User.query.filter_by(email="target.with.data@example.com").first()
        assert target_user is not None
        target_user_id = target_user.id

    login(test_client, "user@example.com", "test1234")
    response = test_client.get(f"/users/{target_user_id}/datasets")

    assert response.status_code == 200
    assert b"Cargando datasets..." in response.data
    assert b"Datasets subidos por el usuario" in response.data


def test_api_get_user_datasets_success(db_setup_for_module):
    """
    Prueba que la API devuelve los datos correctos (200 OK).
    """
    test_client = db_setup_for_module
    with test_client.application.app_context():
        target_user = User.query.filter_by(email="target.with.data@example.com").first()
        assert target_user is not None
        target_user_id = target_user.id

    login(test_client, "user@example.com", "test1234")
    response = test_client.get(f"/api/users/{target_user_id}/datasets")
    json_data = response.get_json()

    assert response.status_code == 200
    assert json_data["status"] == "success"
    assert json_data["pagination"]["total_items"] == 2

    tipos = {item["type"] for item in json_data["data"]}
    assert "uvl" in tipos
    assert "tabular" in tipos


def test_api_get_user_datasets_empty(db_setup_for_module):
    """
    Prueba que la API devuelve una lista vacía para un usuario sin datasets.
    """
    test_client = db_setup_for_module
    with test_client.application.app_context():
        target_empty = User.query.filter_by(email="target.empty@example.com").first()
        assert target_empty is not None
        target_empty_id = target_empty.id

    login(test_client, "user@example.com", "test1234")
    response = test_client.get(f"/api/users/{target_empty_id}/datasets")
    json_data = response.get_json()

    assert response.status_code == 200
    assert json_data["status"] == "success"
    assert json_data["pagination"]["total_items"] == 0


def test_api_get_user_datasets_user_not_found(db_setup_for_module):
    """
    Prueba que la API devuelve un 404 si el usuario no existe.
    """
    test_client = db_setup_for_module
    login(test_client, "user@example.com", "test1234")

    response = test_client.get("/api/users/id-que-no-existe-999/datasets")
    json_data = response.get_json()

    assert response.status_code == 404
    assert json_data["status"] == "error"
