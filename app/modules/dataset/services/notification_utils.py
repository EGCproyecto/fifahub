from typing import Optional

from app.modules.dataset.models import Author, DataSet


def get_dataset_primary_author(dataset: DataSet) -> Optional[Author]:
    """Return the first Author associated with the dataset metadata, if any."""
    try:
        metadata = getattr(dataset, "ds_meta_data", None)
        authors = getattr(metadata, "authors", None)
        if authors:
            return authors[0]
    except Exception:
        return None
    return None


def get_dataset_community_id(dataset: DataSet) -> Optional[str]:
    """Best-effort extraction of a community identifier from a dataset."""
    for attr in ("community_id", "community", "namespace"):
        val = getattr(dataset, attr, None)
        if isinstance(val, str) and val.strip():
            return val.strip()

    try:
        metadata = getattr(dataset, "ds_meta_data", None)
        for attr in ("community_id", "community", "namespace"):
            val = getattr(metadata, attr, None)
            if isinstance(val, str) and val.strip():
                return val.strip()
        tags = getattr(metadata, "tags", None)
        if isinstance(tags, str) and tags.strip():
            for raw_tag in tags.split(","):
                tag = raw_tag.strip()
                if not tag:
                    continue
                if tag.lower().startswith("community:"):
                    return tag.split(":", 1)[1].strip() or None
    except Exception:
        return None

    return None
