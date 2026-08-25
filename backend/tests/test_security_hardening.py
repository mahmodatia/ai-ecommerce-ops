from app.core.config import get_settings
from app.core.errors import public_error_detail


def test_external_error_details_are_redacted_in_production():
    settings = get_settings()
    original_env = settings.app_env
    try:
        settings.app_env = "production"
        detail = public_error_detail(
            "Gmail inbox failed",
            RuntimeError("token=/home/user/secret-token.json"),
        )
        assert detail == "Gmail inbox failed"
        assert "secret-token" not in detail
    finally:
        settings.app_env = original_env


def test_external_error_details_are_visible_in_development():
    settings = get_settings()
    original_env = settings.app_env
    try:
        settings.app_env = "development"
        detail = public_error_detail(
            "Shopify request failed",
            RuntimeError("connection refused"),
        )
        assert "connection refused" in detail
    finally:
        settings.app_env = original_env
