from app import db
from app.modules.dataset.models import BaseDataset, DSMetaData, TabularDataset, UVLDataset


def test_polymorphic_query_returns_subclasses(app):
    with app.app_context():
        md1 = DSMetaData(title="UVL one", description="...", publication_type="book")
        md2 = DSMetaData(title="Tab one", description="...", publication_type="book")
        db.session.add_all([md1, md2])
        db.session.flush()

        u = UVLDataset(user_id=1, ds_meta_data_id=md1.id)
        t = TabularDataset(user_id=1, ds_meta_data_id=md2.id, rows_count=10, schema_json='{"c":3}')
        db.session.add_all([u, t])
        db.session.commit()

        items = BaseDataset.query.order_by(BaseDataset.id).all()
        assert len(items) == 2
        assert isinstance(items[0], (UVLDataset, TabularDataset))
        assert isinstance(items[1], (UVLDataset, TabularDataset))
