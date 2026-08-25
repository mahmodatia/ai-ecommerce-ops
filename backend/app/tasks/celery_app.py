from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery = Celery(
    "ecommerce_ops",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.jobs"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

if settings.gmail_auto_poll:
    celery.conf.beat_schedule = {
        "sync-gmail-inbox": {
            "task": "app.tasks.jobs.sync_gmail_inbox_task",
            "schedule": max(60, settings.gmail_poll_seconds),
        }
    }
