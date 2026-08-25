from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_version: str = "3.0.0"
    api_prefix: str = "/api/v1"
    cors_origins: str = (
        "http://127.0.0.1:5500,"
        "http://localhost:5500,"
        "http://localhost:3000"
    )
    database_url: str = "sqlite:///./dev.db"

    ai_provider: Literal["rules", "openai"] = "rules"
    ai_fallback_to_rules: bool = True
    openai_api_key: str | None = None
    openai_model: str = ""
    prompt_version: str = "email_understanding_v1"
    low_confidence_threshold: float = 0.75

    shopify_mode: Literal["mock", "live"] = "mock"
    shopify_shop: str | None = None
    shopify_client_id: str | None = None
    shopify_client_secret: str | None = None
    shopify_api_version: str = "2026-07"

    gmail_mode: Literal["mock", "live"] = "mock"
    gmail_credentials_file: str = "credentials.json"
    gmail_token_file: str = "token.json"
    gmail_query: str = "in:inbox is:unread"
    gmail_support_only: bool = True
    gmail_max_body_chars: int = 5000
    gmail_manual_send_enabled: bool = False

    external_api_retries: int = 3
    external_api_timeout_seconds: float = 20.0

    redis_url: str = "redis://localhost:6379/0"
    tasks_mode: Literal["sync", "celery"] = "sync"
    gmail_auto_poll: bool = False
    gmail_poll_seconds: int = 300

    data_retention_days: int = 30
    policy_version: str = "1.0"

    log_level: str = "INFO"
    log_json: bool = False

    # Optional private deployment guard. Keep off for local/demo usage.
    auth_mode: Literal["off", "password"] = "off"
    admin_username: str = "admin"
    admin_password: str | None = None
    session_secret: str | None = None
    session_ttl_minutes: int = 480

    # Financial/order mutations remain disabled in this release.
    allow_live_actions: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            item.strip()
            for item in self.cors_origins.split(",")
            if item.strip()
        ]

    @property
    def environment_mode(self) -> str:
        if self.gmail_mode == "live" and self.shopify_mode == "live":
            return "live"
        if self.gmail_mode == "mock" and self.shopify_mode == "mock":
            return "demo"
        return "mixed"


@lru_cache
def get_settings() -> Settings:
    return Settings()
