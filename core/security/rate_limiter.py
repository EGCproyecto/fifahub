import threading
import time
from typing import Tuple

_lock = threading.Lock()
_store: dict[str, dict[str, float | int]] = {}


def check_rate_limit(scope: str, identifier: str, limit: int, window_seconds: int) -> Tuple[bool, int]:
    """
    Returns tuple (limited, retry_after_seconds).
    """
    if limit <= 0:
        return False, 0
    if window_seconds <= 0:
        window_seconds = 60
    identifier = identifier or "unknown"
    key = f"{scope}:{identifier}"
    now = time.time()
    with _lock:
        record = _store.get(key)
        if not record or record["expires_at"] <= now:
            _store[key] = {"count": 1, "expires_at": now + window_seconds}
            return False, window_seconds
        if record["count"] >= limit:
            retry_after = max(1, int(record["expires_at"] - now))
            return True, retry_after
        record["count"] += 1
        retry_after = max(1, int(record["expires_at"] - now))
        _store[key] = record
    return False, retry_after


def reset_rate_limits():
    with _lock:
        _store.clear()
