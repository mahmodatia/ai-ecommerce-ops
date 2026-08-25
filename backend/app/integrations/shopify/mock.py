import json
from pathlib import Path

from app.domain.models import Order


class MockShopify:
    def __init__(self, path: Path):
        self.path = path

    def _all(self):
        return [
            Order.model_validate(x)
            for x in json.loads(self.path.read_text(encoding="utf-8"))
        ]

    def find_by_order_number(self, order_number: str):
        return next(
            (o for o in self._all() if o.order_number == order_number),
            None,
        )

    def list_recent_orders(self, limit: int = 10):
        orders = sorted(self._all(), key=lambda order: order.placed_at, reverse=True)
        return [
            {
                "id": order.id,
                "name": order.order_number,
                "createdAt": order.placed_at.isoformat(),
                "displayFinancialStatus": order.financial_status.upper(),
                "displayFulfillmentStatus": order.fulfillment_status.upper(),
                "customer": {
                    "displayName": order.customer.name,
                    "email": order.customer.email,
                },
                "totalAmount": order.total_amount,
                "currency": order.currency,
                "trackingNumber": order.tracking_number,
                "source": "mock",
            }
            for order in orders[: max(1, min(limit, 25))]
        ]
