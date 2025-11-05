# app/modules/dataset/tests/test_versioning.py

from app import db
from app.modules.auth.models import User
from app.modules.dataset.models import DataSet, DSMetaData, PublicationType
from app.modules.dataset.services.versioning_service import VersioningService
from app.modules.featuremodel.models import FeatureModel
from app.modules.hubfile.models import Hubfile


def test_version_bumps_and_metrics(test_app, clean_database):
    with test_app.app_context():
        # --- Usuario dummy para FK, sin tocar is_active (no tiene setter) ---
        user = User()
        if hasattr(User, "email"):
            user.email = "dummy@example.com"
        if hasattr(user, "set_password"):
            user.set_password("x12345")
        else:
            if hasattr(User, "password"):
                user.password = "x12345"
            if hasattr(User, "password_hash"):
                user.password_hash = "x"

        db.session.add(user)
        db.session.commit()

        # --- DSMetaData con mínimos requeridos ---
        dsmd = DSMetaData(
            title="Dummy title",
            description="Dummy description",
            publication_type=PublicationType.OTHER,
        )
        db.session.add(dsmd)
        db.session.commit()

        # --- DataSet con FK a user y ds_meta_data ---
        ds = DataSet(user_id=user.id, ds_meta_data_id=dsmd.id)
        db.session.add(ds)
        db.session.commit()

        # --- FeatureModel + un CSV de prueba ---
        fm = FeatureModel(data_set_id=ds.id)
        db.session.add(fm)
        db.session.commit()

        hf = Hubfile(name="data.csv", feature_model_id=fm.id, size=10, checksum="x")
        db.session.add(hf)
        db.session.commit()

        # --- Versionado ---
        v1 = VersioningService().create_version(ds, strategy="tabular")
        v2 = VersioningService().create_version(ds, strategy="tabular")

        assert v1.version == "1.0.0"
        assert v2.version == "1.0.1"
        assert isinstance(v2.snapshot, dict)
        assert "metrics" in v2.snapshot
