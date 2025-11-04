from app import db
from app.modules.dataset.models import DataSet
from app.modules.featuremodel.models import FeatureModel
from app.modules.hubfile.models import Hubfile
from app.modules.dataset.services.versioning_service import VersioningService

def test_version_bumps_and_metrics(app_context):
    ds = DataSet(user_id=1)  # ajusta constructor según tu modelo
    db.session.add(ds); db.session.commit()

    fm = FeatureModel(data_set_id=ds.id)
    db.session.add(fm); db.session.commit()

    hf = Hubfile(name="data.csv", feature_model_id=fm.id, size=10, checksum="x")
    db.session.add(hf); db.session.commit()

    v1 = VersioningService().create_version(ds, strategy="tabular")
    v2 = VersioningService().create_version(ds, strategy="tabular")

    assert v1.version == "1.0.0"
    assert v2.version == "1.0.1"
    assert "metrics" in v2.metadata
