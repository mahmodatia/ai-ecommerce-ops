from app.core.auth import create_session_token, verify_credentials, verify_session_token
from app.core.config import Settings


def settings():
    return Settings(
        auth_mode="password",
        admin_username="operator",
        admin_password="strong-test-password",
        session_secret="this-is-a-long-session-secret-for-tests",
    )


def test_password_auth_token_roundtrip():
    s = settings()
    assert verify_credentials(s, "operator", "strong-test-password") is True
    assert verify_credentials(s, "operator", "wrong") is False
    token = create_session_token(s, "operator")
    assert verify_session_token(s, token)["sub"] == "operator"
