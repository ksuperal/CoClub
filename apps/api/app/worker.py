"""Standalone worker process — the only thing that actually *executes* background
jobs once DATABASE_URL is set (services/scheduler.py's schedule_* functions just add
jobs to the shared Postgres-backed store; this process is what runs them). Splitting
this out means the API process stays a plain request/response server: running more
than one API replica no longer risks the same job firing twice, since only this one
process ever executes anything.

Run with: `python -m app.worker` (from apps/api — see docker-compose.yml's `worker`
service). Requires DATABASE_URL: a worker with no shared jobstore to read from has
nothing to do, so it fails fast rather than silently idling forever.
"""

import logging

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.blocking import BlockingScheduler

from .config import get_settings
from .services.scheduler import MAX_CONCURRENT_JOBS, WORKER_HEARTBEAT_SECONDS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def _heartbeat() -> None:
    """No-op. A separate scheduler process only wakes up to re-check its jobstore when
    it processes a job it already knows about — a job added by a *different* process
    (the API) gives it no such signal on its own (verified directly: an idle worker
    with no heartbeat never noticed a job added elsewhere, even after 10+ seconds).
    This recurring tick is what makes that discovery actually happen."""


def main() -> None:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is required to run the worker process — without a shared "
            "jobstore, it has nothing to read jobs from. See README.md."
        )

    scheduler = BlockingScheduler(
        jobstores={"default": SQLAlchemyJobStore(url=settings.database_url)},
        executors={"default": ThreadPoolExecutor(MAX_CONCURRENT_JOBS)},
    )
    scheduler.add_job(
        _heartbeat, "interval", seconds=WORKER_HEARTBEAT_SECONDS, id="heartbeat", replace_existing=True
    )
    logger.info("Worker starting — polling every %ss for due jobs.", WORKER_HEARTBEAT_SECONDS)
    scheduler.start()


if __name__ == "__main__":
    main()
