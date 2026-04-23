from datetime import timedelta
from celery import Celery

from app.config import settings

celery_app = Celery(
    "memcoin",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.discover_new", "app.tasks.refresh_pools"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "discover-new": {
            "task": "app.tasks.discover_new.run",
            "schedule": timedelta(seconds=settings.discover_interval_seconds),
        },
        "refresh-pools": {
            "task": "app.tasks.refresh_pools.run",
            "schedule": timedelta(seconds=settings.refresh_interval_seconds),
        },
    },
)
