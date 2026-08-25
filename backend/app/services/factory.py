from pathlib import Path

from app.core.config import get_settings
from app.services.ai.factory import build_ai

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def build_shopify():
    s = get_settings()

    if s.shopify_mode == "live":
        if (
            not s.shopify_shop
            or not s.shopify_client_id
            or not s.shopify_client_secret
        ):
            raise ValueError(
                "Shopify live mode requires SHOPIFY_SHOP, "
                "SHOPIFY_CLIENT_ID and SHOPIFY_CLIENT_SECRET."
            )

        from app.integrations.shopify.live import ShopifyGraphQL

        return ShopifyGraphQL(
            shop=s.shopify_shop,
            client_id=s.shopify_client_id,
            client_secret=s.shopify_client_secret,
            api_version=s.shopify_api_version,
            retries=s.external_api_retries,
            timeout=s.external_api_timeout_seconds,
        )

    from app.integrations.shopify.mock import MockShopify

    return MockShopify(
        DATA_DIR / "mock_shopify_orders.json"
    )


def build_ai_engine():
    return build_ai(get_settings())


def build_gmail():
    s = get_settings()

    if s.gmail_mode == "live":
        from app.integrations.gmail.live import GmailClient

        return GmailClient(
            credentials_file=s.gmail_credentials_file,
            token_file=s.gmail_token_file,
            query=s.gmail_query,
            retries=s.external_api_retries,
            support_only=s.gmail_support_only,
            max_body_chars=s.gmail_max_body_chars,
        )

    from app.integrations.gmail.mock import MockGmail

    return MockGmail(
        DATA_DIR / "mock_customer_emails.json"
    )
