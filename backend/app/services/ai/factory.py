import logging

from app.core.config import Settings
from app.services.ai.rules import RulesEngine

logger = logging.getLogger(__name__)


class FallbackEngine:
    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback

    def analyze(self, message):
        try:
            return self.primary.analyze(message)
        except Exception as exc:
            logger.warning(
                "ai_primary_failed_falling_back provider=%s error_type=%s",
                type(self.primary).__name__,
                type(exc).__name__,
            )
            return self.fallback.analyze(message)


def build_ai(settings: Settings):
    rules = RulesEngine()
    if settings.ai_provider == "rules":
        return rules
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required when AI_PROVIDER=openai")
    if not settings.openai_model:
        raise ValueError("OPENAI_MODEL is required when AI_PROVIDER=openai")
    from app.services.ai.openai_provider import OpenAIEngine

    primary = OpenAIEngine(
        settings.openai_api_key,
        settings.openai_model,
        timeout=settings.external_api_timeout_seconds,
        retries=settings.external_api_retries,
    )
    return FallbackEngine(primary, rules) if settings.ai_fallback_to_rules else primary
