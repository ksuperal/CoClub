"""Phase 3 of the architecture migration hinges on one precise distinction: the API
process's own scheduler must be PAUSED (adds jobs, never executes them) whenever a
shared Postgres jobstore exists for a separate worker process to read from instead, and
must stay ACTIVE (today's original single-process behavior) when it doesn't. This was
verified by hand against apscheduler's actual behavior before writing the fix (see the
plan/PR notes) -- these tests pin that distinction down as a regression check, not a
retest of apscheduler itself.
"""

from apscheduler.schedulers.base import STATE_PAUSED, STATE_RUNNING

import app.services.scheduler as scheduler_module
from app.config import get_settings


def _reset_scheduler(monkeypatch):
    monkeypatch.setattr(scheduler_module, "_scheduler", None)


def test_scheduler_starts_paused_when_database_url_is_set(monkeypatch):
    _reset_scheduler(monkeypatch)
    monkeypatch.setattr(get_settings(), "database_url", "sqlite:///:memory:")

    sched = scheduler_module.get_scheduler()
    try:
        assert sched.state == STATE_PAUSED
    finally:
        sched.shutdown(wait=False)


def test_scheduler_starts_active_without_database_url(monkeypatch):
    _reset_scheduler(monkeypatch)
    monkeypatch.setattr(get_settings(), "database_url", None)

    sched = scheduler_module.get_scheduler()
    try:
        assert sched.state == STATE_RUNNING
    finally:
        sched.shutdown(wait=False)
