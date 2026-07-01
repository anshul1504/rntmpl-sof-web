"""
Field-level encryption utilities for the Cricket Ecosystem Platform.
Sensitive personal identifiers (Aadhaar, PAN, OTP) and tokens must
be encrypted at rest and masked when displayed.
"""
import hashlib
import hmac
import json
import os
from base64 import b64encode, b64decode

from cryptography.fernet import Fernet
from django.conf import settings


def _get_fernet():
    """Derive a Fernet key from the Django SECRET_KEY."""
    raw = settings.SECRET_KEY.encode('utf-8')
    key_material = hashlib.sha256(raw).digest()
    return Fernet(b64encode(key_material))


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string. Returns a base64-encoded Fernet token."""
    if not plaintext:
        return ''
    f = _get_fernet()
    return f.encrypt(plaintext.encode('utf-8')).decode('utf-8')


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a Fernet token back to plaintext."""
    if not ciphertext:
        return ''
    f = _get_fernet()
    return f.decrypt(ciphertext.encode('utf-8')).decode('utf-8')


def hash_for_lookup(value: str) -> str:
    """Return a keyed SHA-256 hex digest for deterministic lookup
    of encrypted fields without revealing the plaintext."""
    raw = settings.SECRET_KEY.encode('utf-8')
    return hmac.new(raw, value.encode('utf-8'), hashlib.sha256).hexdigest()


def mask_value(value: str, visible_chars: int = 4) -> str:
    """Mask a sensitive value, showing only the last `visible_chars` characters."""
    if not value or len(value) <= visible_chars:
        return '*' * (len(value) if value else 0)
    return '*' * (len(value) - visible_chars) + value[-visible_chars:]


# ── OTP helpers ────────────────────────────────────────────────────────

def hash_otp(otp: str, phone_or_email: str) -> str:
    """Hash an OTP with the target address so it can be verified
    without storing the plaintext OTP."""
    raw = f'{otp}:{phone_or_email}:{settings.SECRET_KEY}'.encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def verify_otp(candidate: str, phone_or_email: str, stored_hash: str) -> bool:
    """Compare a candidate OTP against the stored hash."""
    return hmac.compare_digest(
        hash_otp(candidate, phone_or_email),
        stored_hash,
    )
