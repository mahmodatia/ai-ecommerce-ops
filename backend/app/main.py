from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router
from app.core.auth import AuthError, validate_auth_config, verify_session_token
from app.core.config import get_settings
from app.core.logging import request_id_var, setup_logging

logger = logging.getLogger(__name__)


def create_app():
    settings = get_settings()
    setup_logging(level=settings.log_level, json_logs=settings.log_json)

    is_production = settings.app_env.lower() in {"production", "prod"}

    if settings.auth_mode == "password":
        validate_auth_config(settings)
    if (
        is_production
        and settings.environment_mode in {"live", "mixed"}
        and settings.auth_mode != "password"
    ):
        raise RuntimeError("Live or mixed production mode requires AUTH_MODE=password")

    app = FastAPI(
        title="AI E-commerce Operations Automation System",
        version=settings.app_version,
        description=(
            "Review-first AI operations with Gmail, Shopify, deterministic "
            "policy decisions, explainable traces, human approval, draft-first execution, and optional explicitly enabled manual Gmail sending."
        ),
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def auth_guard(request: Request, call_next):
        if settings.auth_mode != "password":
            return await call_next(request)

        public_paths = {
            f"{settings.api_prefix}/health",
            f"{settings.api_prefix}/ready",
            f"{settings.api_prefix}/auth/status",
            f"{settings.api_prefix}/auth/login",
            "/docs",
            "/openapi.json",
        }
        if (
            request.method == "OPTIONS"
            or request.url.path in public_paths
            or request.url.path.startswith("/docs")
        ):
            return await call_next(request)

        if request.url.path.startswith(settings.api_prefix):
            authorization = request.headers.get("Authorization", "")
            if not authorization.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required"},
                )
            try:
                payload = verify_session_token(
                    settings,
                    authorization.removeprefix("Bearer ").strip(),
                )
                request.state.user = payload.get("sub", "operator")
            except AuthError as exc:
                return JSONResponse(status_code=401, content={"detail": str(exc)})

        return await call_next(request)

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid4().hex[:16]
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                "http_request method=%s path=%s status=%s",
                request.method,
                request.url.path,
                response.status_code,
            )
            return response
        except Exception:
            logger.exception(
                "http_request_failed method=%s path=%s",
                request.method,
                request.url.path,
            )
            raise
        finally:
            request_id_var.reset(token)

    app.include_router(router, prefix=settings.api_prefix)
    return app


app = create_app()
