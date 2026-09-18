"""Durable delayed-job scheduler for the Step 5 feedback job, the metrics-polling job,
video polling, and (since Phase 2) media generation.

APScheduler with a Postgres-backed jobstore. When DATABASE_URL is set, this process
(the API) only ever *adds* jobs — its own scheduler is started paused and never
resumed, so it never executes anything itself. A separate worker process
(app/worker.py, `python -m app.worker`) is what actually runs jobs, reading from the
same Postgres-backed store. This is what lets more than one API replica run safely:
only the one worker process ever executes a given job, so nothing can fire twice.

Without DATABASE_URL, there's no store a separate process could read from anyway (an
in-memory jobstore is only visible within the process that created it), so this
process's own scheduler starts unpaused and executes jobs itself instead — the same
single-process behavior this had before the worker split, for local dev.

Two deliberate anti-thundering-herd measures, since many campaigns' polling jobs can
land on the same interval boundary once there's real traffic (everyone tends to post
during business hours, so their 6-hourly polls would otherwise all cluster together):
- A bounded thread pool (MAX_CONCURRENT_JOBS) caps how many jobs run *at once*,
  regardless of how many are technically due at the same moment — the rest queue and
  drain through a fixed number of workers instead of firing simultaneously.
- Jitter on each campaign's polling schedule spreads otherwise-simultaneous jobs
  across a window instead of syncing them to the same instant.

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

VIDEO_POLL_INTERVAL_SECONDS = 15  # much tighter than the metrics poll — a variant sits
# blocked in 'generating' (can't be approved/posted) until this resolves, unlike metrics
# which are purely informational
VIDEO_POLL_MAX_MINUTES = 30  # give up and mark the variant 'failed' rather than poll forever
# if Luma never reaches a terminal status

WORKER_HEARTBEAT_SECONDS = 3  # app/worker.py's no-op recurring job — see its own
# docstring for why this exists: a separate scheduler process doesn't otherwise notice
# a job added by a different process at all, verified directly against apscheduler's
# actual behavior (not merely assumed from its docs).


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        settings = get_settings()
        db_url = settings.database_url
        jobstores = {"default": SQLAlchemyJobStore(url=db_url)} if db_url else {}
        executors = {"default": ThreadPoolExecutor(MAX_CONCURRENT_JOBS)}
        _scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors)
        # Paused when there's a shared (Postgres) jobstore for a worker process to
        # execute from instead — never resumed, this process only adds jobs from here
        # on. Without one, there's nothing else that could run them, so this same
        # scheduler stays unpaused and executes them itself, as before the split.
        _scheduler.start(paused=bool(db_url))
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


def schedule_variant_media_generation(campaign_id: str, user_id: str, variant_ids: list[str]) -> None:
    """One-shot, immediate background job — decouples the expensive image/video
    generation loop (gpt-image-2 + quality-check calls, several per variant) from
    the HTTP request that kicked it off, so a multi-variant campaign can never hold
    a request open past a reverse proxy's timeout. Reuses the same scheduler/jobstore
    as everything else here — durable across a process restart when DATABASE_URL is
    set, in-memory-only otherwise, same as today."""
    from ..pipeline.step2_variants import run_variant_media_generation_job

    get_scheduler().add_job(
        run_variant_media_generation_job,
        "date",
        run_date=datetime.now(timezone.utc),
        args=[campaign_id, user_id, variant_ids],
        id=f"generate-media-{campaign_id}",
        replace_existing=True,
    )


def schedule_video_generation_poll(variant_id: str) -> None:
    """Polls one Luma video-generation job until it resolves. Much tighter
    interval than metrics polling since a variant sits blocked in 'generating'
    (can't be approved/posted) until this finishes, not just informational.

    Self-canceling: the job function (poll_video_generation_job) removes its own
    APScheduler job once it sees a terminal status. The `end_date` here is set one
    interval past the real deadline (passed separately as `deadline_iso`) so a
    final tick still fires *after* the deadline has passed — otherwise IntervalTrigger
    would simply stop scheduling at end_date without ever calling the job function to
    mark it failed, leaving it stuck in 'generating' forever if Luma never
    resolves."""
    from ..pipeline.step2_variants import poll_video_generation_job

    now = datetime.now(timezone.utc)
    deadline = now + timedelta(minutes=VIDEO_POLL_MAX_MINUTES)
    get_scheduler().add_job(
        poll_video_generation_job,
        "interval",
        seconds=VIDEO_POLL_INTERVAL_SECONDS,
        start_date=now + timedelta(seconds=VIDEO_POLL_INTERVAL_SECONDS),
        end_date=deadline + timedelta(seconds=VIDEO_POLL_INTERVAL_SECONDS),
        args=[variant_id, deadline.isoformat()],
        id=f"video-poll-{variant_id}",
        replace_existing=True,
    )
