"""Durable delayed-job scheduler for the Step 5 feedback job.

APScheduler with a Postgres-backed jobstore, running inside the FastAPI process — an
MVP simplification instead of standing up a separate Node service (BullMQ/Trigger.dev)
for one delayed job. Jobs survive a process restart since they're persisted in Postgres.
"""

from datetime import timedelta, timezone, datetime

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from ..config import get_settings

_scheduler: BackgroundScheduler | None = None

FEEDBACK_DELAY_HOURS = 24


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        settings = get_settings()
        db_url = settings.database_url
        jobstores = {"default": SQLAlchemyJobStore(url=db_url)} if db_url else {}
        _scheduler = BackgroundScheduler(jobstores=jobstores)
        _scheduler.start()
    return _scheduler


def schedule_feedback_job(campaign_id: str, *, delay_hours: int = FEEDBACK_DELAY_HOURS) -> None:
    from ..pipeline.step5_feedback import run_feedback_job  # local import avoids a cycle

    run_at = datetime.now(timezone.utc) + timedelta(hours=delay_hours)
    get_scheduler().add_job(
        run_feedback_job,
        "date",
        run_date=run_at,
        args=[campaign_id],
        id=f"feedback-{campaign_id}",
        replace_existing=True,
    )
