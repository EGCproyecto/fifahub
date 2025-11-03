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
