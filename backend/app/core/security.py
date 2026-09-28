from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from app.core.config import settings

ALGORITHM = "HS256"
PBKDF2_ITERATIONS = 390_000


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def hash_password(password: str) -> str:
    if not 10 <= len(password) <= 128:
        raise ValueError("Password must be between 10 and 128 characters")
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64url_encode(salt)}${_b64url_encode(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt_value, digest_value = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return _verify_legacy_password(password, encoded)
        salt = _b64url_decode(salt_value)
        expected = _b64url_decode(digest_value)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _verify_legacy_password(password: str, encoded: str) -> bool:
    """Best-effort support for legacy bcrypt hashes when passlib is installed."""
    if not encoded.startswith(("$2a$", "$2b$", "$2y$")):
        return False
    try:
        from passlib.context import CryptContext  # type: ignore

        return CryptContext(schemes=["bcrypt"]).verify(password, encoded)
    except Exception:
        return False


def create_access_token(subject: str, organization_id: str, role: str) -> str:
    now = int(time.time())
    payload = {
        "sub": subject,
        "org": organization_id,
        "role": role,
        "iat": now,
        "exp": now + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "iss": settings.TOKEN_ISSUER,
        "aud": settings.TOKEN_AUDIENCE,
        "jti": secrets.token_urlsafe(16),
    }
    header = {"alg": ALGORITHM, "typ": "JWT"}
    segments = [
        _b64url_encode(json.dumps(header, separators=(",", ":")).encode()),
        _b64url_encode(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments).encode("ascii")
    signature = hmac.new(settings.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return ".".join([*segments, _b64url_encode(signature)])


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
        signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
        expected = hmac.new(settings.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64url_decode(signature_segment)):
            raise ValueError("Invalid token signature")
        header = json.loads(_b64url_decode(header_segment))
        payload = json.loads(_b64url_decode(payload_segment))
        if header.get("alg") != ALGORITHM:
            raise ValueError("Invalid token algorithm")
        if payload.get("exp", 0) <= int(time.time()):
            raise ValueError("Token expired")
        if payload.get("iss") != settings.TOKEN_ISSUER or payload.get("aud") != settings.TOKEN_AUDIENCE:
            raise ValueError("Invalid token audience")
        if not payload.get("sub") or not payload.get("org"):
            raise ValueError("Invalid token claims")
        return payload
    except Exception as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError("Invalid token") from exc
