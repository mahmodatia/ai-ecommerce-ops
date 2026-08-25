import _bootstrap  # noqa: F401
from pathlib import Path

from app.core.config import get_settings


def yes_no(value):
    return "OK" if value else "MISSING"


def main():
    settings = get_settings()

    print(f"AI E-commerce Ops {settings.app_version} preflight")
    print("-" * 48)
    print(f"Environment: {settings.environment_mode}")
    print(f"AI provider: {settings.ai_provider}")

    if settings.ai_provider == "openai":
        print("OpenAI key:", yes_no(bool(settings.openai_api_key)))
        print("OpenAI model:", yes_no(bool(settings.openai_model)))

    print(f"Shopify mode: {settings.shopify_mode}")
    if settings.shopify_mode == "live":
        print("Shop:", yes_no(bool(settings.shopify_shop)))
        print("Shopify Client ID:", yes_no(bool(settings.shopify_client_id)))
        print("Shopify Client Secret:", yes_no(bool(settings.shopify_client_secret)))

    print(f"Gmail mode: {settings.gmail_mode}")
    if settings.gmail_mode == "live":
        print(
            "credentials.json:",
            yes_no(Path(settings.gmail_credentials_file).exists()),
        )
        print("token.json:", yes_no(Path(settings.gmail_token_file).exists()))

    print(f"Tasks mode: {settings.tasks_mode}")
    print(f"Database: {settings.database_url.split(':', 1)[0]}")
    print(f"Auth mode: {settings.auth_mode}")
    if settings.auth_mode == "password":
        print("Admin password:", yes_no(bool(settings.admin_password)))
        print(
            "Session secret:",
            yes_no(bool(settings.session_secret and len(settings.session_secret) >= 24)),
        )

    print("Gmail automatic send: DISABLED")
    print("Gmail reviewed manual send:", "ENABLED" if settings.gmail_manual_send_enabled else "DISABLED")
    print("Shopify live mutations: DISABLED")


if __name__ == "__main__":
    main()
