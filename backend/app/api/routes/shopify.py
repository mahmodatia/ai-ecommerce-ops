from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.core.errors import public_error_detail
from app.services.factory import build_shopify

router = APIRouter()


@router.get("/status")
def shopify_status():
    settings = get_settings()
    return {
        "mode": settings.shopify_mode,
        "shop": settings.shopify_shop,
        "configured": bool(
            settings.shopify_mode == "mock"
            or (
                settings.shopify_shop
                and settings.shopify_client_id
                and settings.shopify_client_secret
            )
        ),
        "read_only": True,
        "mutations": False,
    }


@router.get("/orders")
def recent_orders(limit: int = 10):
    try:
        return build_shopify().list_recent_orders(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=public_error_detail("Shopify request failed", exc)) from exc
