from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

# Base de datos en memoria
DB: Dict[str, "Deposition"] = {}


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass
class Version:
    recid: str
    version: int
    doi: Optional[str]
    files: Dict[str, bytes] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)
    created: str = field(default_factory=_now_iso)
    state: str = "draft"


@dataclass
class Deposition:
    id: str
    conceptrecid: str
    versions: List[Version] = field(default_factory=list)


def create_deposition(initial_metadata: dict) -> Deposition:
    dep_id = f"d_{uuid.uuid4().hex[:8]}"
    conceptrecid = f"c_{uuid.uuid4().hex[:8]}"
    draft = Version(
        recid=f"r_{uuid.uuid4().hex[:8]}",
        version=0,
        doi=None,
        metadata=initial_metadata or {},
    )
    dep = Deposition(id=dep_id, conceptrecid=conceptrecid, versions=[draft])
    DB[dep_id] = dep
    return dep


def get_deposition(dep_id: str) -> Optional[Deposition]:
    return DB.get(dep_id)


def update_metadata(dep_id: str, metadata: dict) -> Version:
    dep = DB[dep_id]
    draft = dep.versions[0]
    draft.metadata = metadata or {}
    return draft


def put_file(dep_id: str, filename: str, content: bytes) -> Version:
    dep = DB[dep_id]
    draft = dep.versions[0]
    draft.files[filename] = content
    return draft


def add_published_version(dep_id: str, published: Version) -> Version:
    dep = DB[dep_id]
    dep.versions.append(published)
    return published


def list_versions(dep_id: str) -> Dict:
    dep = DB[dep_id]
    return {
        "conceptrecid": dep.conceptrecid,
        "versions": [
            {
                "recid": v.recid,
                "version": v.version,
                "state": v.state,
                "doi": v.doi,
                "created": v.created,
            }
            for v in dep.versions
        ],
    }
