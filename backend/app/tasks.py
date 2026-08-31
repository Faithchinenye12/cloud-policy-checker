from celery import Celery

from backend.app.scans.service import execute_scan
from config import settings


celery_app = Celery(
    "cloud_policy_checker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(
    bind=True,
    name="backend.app.tasks.run_scan_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_scan_task(
    self,
    scan_id: int,
) -> dict:
    """Run one deterministic compliance scan in a Celery worker."""
    _ = self
    return execute_scan(scan_id)