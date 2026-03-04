"""
Cryptographic utilities for MindFlow/Rovot.

Provides symmetric encryption for storing sensitive credentials
(email passwords, API keys) in the database. Uses Fernet (AES-128-CBC)
from the ``cryptography`` library.

The encryption key is derived from the application's ``SECRET_KEY``
environment variable using PBKDF2.

Usage::

    from src.crypto import encrypt_value, decrypt_value

    encrypted = encrypt_value("my-secret-password")
    original  = decrypt_value(encrypted)
"""
from __future__ import annotations

import base64
import hashlib
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy initialisation of the Fernet cipher
_fernet = None


def _get_fernet():
    """Return a Fernet instance derived from SECRET_KEY."""
    global _fernet
    if _fernet is not None:
        return _fernet

    secret = os.environ.get("SECRET_KEY") or os.environ.get("JWT_SECRET_KEY", "")
    if not secret:
        raise RuntimeError(
            "SECRET_KEY or JWT_SECRET_KEY must be set for credential encryption."
        )

    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes

        # Derive a 32-byte key from the secret using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"mindflow-rovot-salt-v1",  # Fixed salt (key is already random)
            iterations=100_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode("utf-8")))
        _fernet = Fernet(key)
        return _fernet

    except ImportError:
        logger.warning(
            "cryptography package not installed. "
            "Falling back to base64 encoding (NOT SECURE for production)."
        )
        return None


def encrypt_value(plaintext: str) -> str:
    """
    Encrypt a string value.

    Returns a base64-encoded ciphertext string suitable for database storage.
    Falls back to base64 encoding if ``cryptography`` is not installed.
    """
    if not plaintext:
        return ""

    fernet = _get_fernet()
    if fernet:
        return fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    # Fallback: base64 (NOT secure, but functional)
    return "b64:" + base64.b64encode(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(ciphertext: str) -> str:
    """
    Decrypt a previously encrypted value.

    Returns the original plaintext string.
    """
    if not ciphertext:
        return ""

    # Handle base64 fallback
    if ciphertext.startswith("b64:"):
        return base64.b64decode(ciphertext[4:]).decode("utf-8")

    fernet = _get_fernet()
    if fernet:
        try:
            return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
        except Exception as exc:
            logger.error("Decryption failed: %s", exc)
            return ""

    return ""


def is_encrypted(value: str) -> bool:
    """Check if a value appears to be encrypted."""
    if not value:
        return False
    if value.startswith("b64:"):
        return True
    # Fernet tokens start with 'gAAAAA'
    return value.startswith("gAAAAA")
