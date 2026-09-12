"""Durable delayed-job scheduler for the Step 5 feedback job and the metrics-polling
job.

APScheduler with a Postgres-backed jobstore, running inside the FastAPI process — an
MVP simplification instead of standing up a separate Node service (BullMQ/Trigger.dev).
Jobs survive a process restart since they're persisted in Postgres.

Two deliberate anti-thundering-herd measures, since many campaigns' polling jobs can
land on the same interval boundary once there's real traffic (everyone tends to post
during business hours, so their 6-hourly polls would otherwise all cluster together):
- A bounded thread pool (MAX_CONCURRENT_JOBS) caps how many jobs run *at once*,
  regardless of how many are technically due at the same moment — the rest queue and
  drain through a fixed number of workers instead of firing simultaneously.
- Jitter on each campaign's polling schedule spreads otherwise-simultaneous jobs
  across a window instead of syncing them to the same instant.
"""

import random
from datetime import timedelta, timezone, datetime

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from ..config import get_settings

_scheduler: BackgroundScheduler | None = None

FEEDBACK_DELAY_HOURS = 24
METRICS_POLL_INTERVAL_HOURS = 1
METRICS_POLL_DURATION_HOURS = 72  # most organic engagement lands in the first few days
METRICS_POLL_JITTER_MINUTES = 15  # spread otherwise-simultaneous polls across this window
MAX_CONCURRENT_JOBS = 5  # bounds outbound API call concurrency regardless of burst size


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        settings = get_settings()
        db_url = settings.database_url
        jobstores = {"default": SQLAlchemyJobStore(url=db_url)} if db_url else {}
        executors = {"default": ThreadPoolExecutor(MAX_CONCURRENT_JOBS)}
        _scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors)
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


def schedule_metrics_polling(campaign_id: str) -> None:
    """Auto-refreshes metrics (no LLM — just the platform API calls) every
    METRICS_POLL_INTERVAL_HOURS for METRICS_POLL_DURATION_HOURS after posting, so the
    graph stays current without anyone having to click "Refresh metrics." Stops
    firing on its own after the duration window — APScheduler drops a job once its
    trigger's end_date has passed, no manual cleanup needed.

    The jitter is applied once, to start_date — since IntervalTrigger fires at
    start_date + n*interval, shifting start_date shifts every later tick for this
    campaign by the same random offset, so its whole polling schedule (not just the
    first tick) is de-synced from other campaigns that happened to post nearby."""
    from ..pipeline.step5_feedback import run_scheduled_metrics_refresh  # local import avoids a cycle

    now = datetime.now(timezone.utc)
    jitter = timedelta(minutes=random.randint(-METRICS_POLL_JITTER_MINUTES, METRICS_POLL_JITTER_MINUTES))
    first_run = now + timedelta(hours=METRICS_POLL_INTERVAL_HOURS) + jitter  # first tick at +6h, not immediately (nothing to see at t=0)
    get_scheduler().add_job(
        run_scheduled_metrics_refresh,
        "interval",
        hours=METRICS_POLL_INTERVAL_HOURS,
        start_date=first_run,
        end_date=now + timedelta(hours=METRICS_POLL_DURATION_HOURS),
        args=[campaign_id],
        id=f"metrics-poll-{campaign_id}",
        replace_existing=True,
    )
