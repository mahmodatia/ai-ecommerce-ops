import _bootstrap  # noqa: F401
from app.core.config import get_settings
from app.services.factory import build_shopify


def main():
    settings = get_settings()

    if settings.shopify_mode != "live":
        raise SystemExit("Set SHOPIFY_MODE=live in backend/.env first.")

    print(f"Shop: {settings.shopify_shop}.myshopify.com")
    print("Authenticating with Shopify...")

    orders = build_shopify().list_recent_orders(limit=10)

    print("Authentication: OK")
    print(f"Orders returned: {len(orders)}")

    for order in orders:
        customer = order.get("customer") or {}
        print(
            f"- {order['name']} | "
            f"{order['displayFinancialStatus']} | "
            f"{order['displayFulfillmentStatus']} | "
            f"{customer.get('displayName') or 'No customer'}"
        )


if __name__ == "__main__":
    main()
