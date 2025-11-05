from app import create_app, db
from app.modules.auth.models import User
from app.modules.dataset.models import (
    BaseDataset,
    DSMetaData,
    PublicationType,
    UVLDataset,
)
from app.modules.tabular.models import TabularDataset


def test_polymorphic_query_returns_subclasses():
    app = create_app()
    with app.app_context():
        # Crear esquema para este test (tablas necesarias en la BD de CI)
        db.create_all()
        try:
            # Usuario para FKs
            user = User(email="poly@test.local")
            user.set_password("x")
            db.session.add(user)
            db.session.flush()

            # Metadatos (usar Enum, no string)
            md1 = DSMetaData(
                title="UVL one",
                description="...",
                publication_type=PublicationType.BOOK,
            )
            md2 = DSMetaData(
                title="Tab one",
                description="...",
                publication_type=PublicationType.BOOK,
            )
            db.session.add_all([md1, md2])
            db.session.flush()

            # Una instancia de cada subclase
            u = UVLDataset(user_id=user.id, ds_meta_data_id=md1.id)
            t = TabularDataset(
                user_id=user.id,
                ds_meta_data_id=md2.id,
                rows_count=10,
                schema_json='{"c":3}',
            )
            db.session.add_all([u, t])
            db.session.commit()

            # Verificación polimórfica
            items = (
                BaseDataset.query.filter(BaseDataset.id.in_([u.id, t.id]))
                .order_by(BaseDataset.id)
                .all()
            )
            assert type(items[0]) is UVLDataset
            assert type(items[1]) is TabularDataset
        finally:
            # Limpieza del esquema para no dejar residuos en CI
            db.session.rollback()
            db.drop_all()
