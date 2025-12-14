from __future__ import annotations

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken

_fernet_instance: Fernet | None = None


def _build_key() -> bytes:
    key_source = os.getenv("TWO_FACTOR_ENCRYPTION_KEY") or os.getenv("SECRET_KEY")
    if not key_source:
        raise RuntimeError("TWO_FACTOR_ENCRYPTION_KEY or SECRET_KEY must be defined")
    if isinstance(key_source, bytes):
        key_source = key_source.decode()
    digest = hashlib.sha256(key_source.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def _fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        _fernet_instance = Fernet(_build_key())
    return _fernet_instance


def encrypt_text(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_text(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()


__all__ = ["encrypt_text", "decrypt_text", "InvalidToken"]
