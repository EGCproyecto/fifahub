from typing import Type

from app import db
from app.modules.dataset.models import BaseDataset, TabularDataset, UVLDataset

_TYPE_MAP: dict[str, Type[BaseDataset]] = {
    "uvl": UVLDataset,
    "tabular": TabularDataset,
}


def create_dataset(payload: dict) -> BaseDataset:
    ds_type = payload["type"]
    Model = _TYPE_MAP[ds_type]
    obj = Model(**{k: v for k, v in payload.items() if k != "type"})
    if hasattr(obj, "validate_domain"):
        obj.validate_domain()
    db.session.add(obj)
    db.session.commit()
    return obj
