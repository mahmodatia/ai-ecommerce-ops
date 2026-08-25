from __future__ import annotations

import time
from datetime import datetime
from email.utils import parsedate_to_datetime

import httpx

from app.core.errors import IntegrationError
from app.domain.models import Customer, Order, OrderItem


class ShopifyGraphQL:
    """Read-only Shopify Admin GraphQL gateway."""

    def __init__(
        self,
        shop: str,
        client_id: str,
        client_secret: str,
        api_version: str,
        *,
        retries: int = 3,
        timeout: float = 20.0,
    ):
        clean_shop = shop.removesuffix(".myshopify.com").strip()
        self.base_url = f"https://{clean_shop}.myshopify.com"
        self.graphql_url = (
            f"{self.base_url}/admin/api/{api_version}/graphql.json"
        )
        self.token_url = f"{self.base_url}/admin/oauth/access_token"

        self.client_id = client_id
        self.client_secret = client_secret
        self.retries = max(0, retries)
        self.timeout = timeout

        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    def _sleep_for(self, response: httpx.Response | None, attempt: int) -> None:
        delay = min(2 ** attempt, 8)

        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    delay = min(float(retry_after), 30)
                except ValueError:
                    try:
                        dt = parsedate_to_datetime(retry_after)
                        delay = max(0, min(dt.timestamp() - time.time(), 30))
                    except Exception:
                        pass

        time.sleep(delay)

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        last_error: Exception | None = None

        for attempt in range(self.retries + 1):
            response = None
            try:
                response = httpx.request(
                    method,
                    url,
                    timeout=self.timeout,
                    **kwargs,
                )

                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < self.retries:
                        self._sleep_for(response, attempt)
                        continue

                response.raise_for_status()
                return response

            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_error = exc

                retriable = (
                    isinstance(exc, httpx.RequestError)
                    or (
                        response is not None
                        and (
                            response.status_code == 429
                            or response.status_code >= 500
                        )
                    )
                )

                if retriable and attempt < self.retries:
                    self._sleep_for(response, attempt)
                    continue
                break

        raise IntegrationError(
            "shopify",
            f"Shopify request failed after retries: "
            f"{type(last_error).__name__ if last_error else 'unknown error'}",
        )

    def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        response = self._request(
            "POST",
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise IntegrationError(
                "shopify",
                "Shopify authentication succeeded but no access token was returned.",
            )

        self._access_token = token
        self._token_expires_at = (
            time.time() + int(payload.get("expires_in", 86399))
        )
        return token

    def _graphql(self, query: str, variables: dict | None = None) -> dict:
        response = self._request(
            "POST",
            self.graphql_url,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self._get_access_token(),
            },
            json={
                "query": query,
                "variables": variables or {},
            },
        )

        payload = response.json()
        if payload.get("errors"):
            messages = [
                item.get("message", "GraphQL error")
                for item in payload["errors"][:3]
            ]
            raise IntegrationError(
                "shopify",
                "Shopify GraphQL error: " + "; ".join(messages),
            )

        return payload["data"]

    def list_recent_orders(self, limit: int = 10) -> list[dict]:
        query = '''
        query RecentOrders($first: Int!) {
          orders(first: $first, sortKey: CREATED_AT, reverse: true) {
            nodes {
              id
              name
              createdAt
              displayFinancialStatus
              displayFulfillmentStatus
              customer {
                displayName
                email
              }
              currentTotalPriceSet {
                shopMoney {
                  amount
                  currencyCode
                }
              }
              fulfillments(first: 5) {
                trackingInfo {
                  number
                  url
                }
              }
            }
          }
        }
        '''

        data = self._graphql(
            query,
            {"first": max(1, min(limit, 25))},
        )
        output = []
        for node in data["orders"]["nodes"]:
            money = (node.get("currentTotalPriceSet") or {}).get("shopMoney") or {}
            fulfillments = node.get("fulfillments") or []
            tracking = {}
            for fulfillment in reversed(fulfillments):
                info = fulfillment.get("trackingInfo") or []
                if info:
                    tracking = info[0]
                    break
            output.append(
                {
                    **node,
                    "totalAmount": float(money["amount"]) if money.get("amount") is not None else None,
                    "currency": money.get("currencyCode"),
                    "trackingNumber": tracking.get("number"),
                    "source": "live",
                }
            )
        return output

    def find_by_order_number(self, order_number: str) -> Order | None:
        query = '''
        query FindOrder($query: String!) {
          orders(first: 1, query: $query) {
            nodes {
              id
              name
              createdAt
              displayFinancialStatus
              displayFulfillmentStatus
              email

              customer {
                displayName
                email
              }

              currentTotalPriceSet {
                shopMoney {
                  amount
                  currencyCode
                }
              }

              lineItems(first: 50) {
                nodes {
                  sku
                  name
                  quantity
                }
              }

              fulfillments(first: 10) {
                updatedAt
                trackingInfo {
                  number
                  url
                }
              }
            }
          }
        }
        '''

        data = self._graphql(
            query,
            {"query": f"name:{order_number}"},
        )
        nodes = data["orders"]["nodes"]

        if not nodes:
            return None

        node = nodes[0]
        customer = node.get("customer") or {}
        money = node["currentTotalPriceSet"]["shopMoney"]

        fulfillments = node.get("fulfillments") or []
        latest = fulfillments[-1] if fulfillments else {}
        tracking_list = latest.get("trackingInfo") or []
        tracking = tracking_list[0] if tracking_list else {}

        display_status = (
            node.get("displayFulfillmentStatus") or ""
        ).upper()

        fulfillment_status = {
            "FULFILLED": "fulfilled",
            "UNFULFILLED": "unfulfilled",
            "IN_PROGRESS": "processing",
            "PARTIALLY_FULFILLED": "processing",
        }.get(display_status, "processing")

        return Order(
            id=node["id"],
            order_number=node["name"],
            customer=Customer(
                name=customer.get("displayName") or "Customer",
                email=(
                    customer.get("email")
                    or node.get("email")
                    or ""
                ),
            ),
            financial_status=(
                node.get("displayFinancialStatus") or "pending"
            ).lower(),
            fulfillment_status=fulfillment_status,
            placed_at=datetime.fromisoformat(
                node["createdAt"].replace("Z", "+00:00")
            ),
            delivered_at=None,
            tracking_status=(
                "in_transit" if fulfillments else None
            ),
            tracking_last_update=(
                datetime.fromisoformat(
                    latest["updatedAt"].replace("Z", "+00:00")
                )
                if latest.get("updatedAt")
                else None
            ),
            tracking_number=tracking.get("number"),
            tracking_url=tracking.get("url"),
            items=[
                OrderItem(
                    sku=item.get("sku") or "",
                    title=item["name"],
                    quantity=item["quantity"],
                )
                for item in node["lineItems"]["nodes"]
            ],
            total_amount=float(money["amount"]),
            currency=money["currencyCode"],
        )
