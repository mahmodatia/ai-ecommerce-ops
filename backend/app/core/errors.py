from __future__ import annotations

from app.core.config import get_settings


class IntegrationError(RuntimeError):
    """Safe external-integration error.

    The message may be returned to the dashboard, so never put secrets
    or full credential payloads in it.
    """

    def __init__(self, service: str, message: str):
        self.service = service
        super().__init__(message)


def public_error_detail(message: str, exc: Exception) -> str:
    """Return useful local diagnostics without leaking internals in production."""
    settings = get_settings()
    if settings.app_env.lower() in {"production", "prod"}:
        return message
    return f"{message}: {exc}"
