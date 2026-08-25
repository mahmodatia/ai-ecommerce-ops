from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

from app.core.config import Settings


class AuthError(ValueError):
    pass


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def validate_auth_config(settings: Settings) -> None:
    if settings.auth_mode != "password":
        return
    if not settings.admin_password:
        raise AuthError("ADMIN_PASSWORD is required when AUTH_MODE=password")
    if not settings.session_secret or len(settings.session_secret) < 24:
        raise AuthError(
            "SESSION_SECRET must be at least 24 characters when AUTH_MODE=password"
        )


def verify_credentials(settings: Settings, username: str, password: str) -> bool:
    validate_auth_config(settings)
    expected_user = settings.admin_username.encode("utf-8")
    expected_password = (settings.admin_password or "").encode("utf-8")
    return secrets.compare_digest(username.encode("utf-8"), expected_user) and secrets.compare_digest(
        password.encode("utf-8"), expected_password
    )


def create_session_token(settings: Settings, username: str) -> str:
    validate_auth_config(settings)
    payload = {
        "sub": username,
        "exp": int(time.time()) + settings.session_ttl_minutes * 60,
    }
    encoded = _b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = hmac.new(
        (settings.session_secret or "").encode("utf-8"),
        encoded.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{encoded}.{_b64encode(signature)}"


def verify_session_token(settings: Settings, token: str) -> dict:
    validate_auth_config(settings)
    try:
        encoded, supplied_sig = token.split(".", 1)
        expected_sig = hmac.new(
            (settings.session_secret or "").encode("utf-8"),
            encoded.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not secrets.compare_digest(_b64decode(supplied_sig), expected_sig):
            raise AuthError("Invalid session token")
        payload = json.loads(_b64decode(encoded))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise AuthError("Session expired")
        return payload
    except (ValueError, json.JSONDecodeError, KeyError) as exc:
        raise AuthError("Invalid session token") from exc
