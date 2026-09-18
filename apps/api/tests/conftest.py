"""Minimal in-memory stand-in for the Supabase client's fluent query builder, and
fixtures wiring it into the app in place of the real service-role client.

Only supports the call shapes routers/brands.py and routers/campaigns.py actually use
(select/insert/update + eq/ilike/order/execute) -- not a general Postgrest
reimplementation. `get_service_client()` is called directly inside route bodies (not
via FastAPI's `Depends`), so it can't be swapped with `app.dependency_overrides` --
each router module's already-bound `get_service_client` name is patched instead via
`monkeypatch`.
"""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.db import get_current_user_id
from app.main import app


class _Result:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, store, table):
        self._store = store
        self._table = table
        self._filters = []
        self._order = None
        self._op = None
        self._payload = None

    def select(self, *_args, **_kwargs):
        self._op = self._op or "select"
        return self

    def insert(self, payload):
        self._op = "insert"
        self._payload = payload
        return self

    def update(self, payload):
        self._op = "update"
        self._payload = payload
        return self

    def eq(self, key, value):
        self._filters.append(("eq", key, value))
        return self

    def ilike(self, key, value):
        self._filters.append(("ilike", key, value))
        return self

    def order(self, key, desc=False):
        self._order = (key, desc)
        return self

    def _matches(self, row):
        for kind, key, value in self._filters:
            if kind == "eq" and row.get(key) != value:
                return False
            if kind == "ilike" and str(row.get(key, "")).lower() != str(value).lower():
                return False
        return True

    def execute(self):
        rows = self._store.setdefault(self._table, [])
        if self._op == "select":
            matched = [dict(r) for r in rows if self._matches(r)]
            if self._order:
                key, desc = self._order
                matched.sort(key=lambda r: r.get(key), reverse=desc)
            return _Result(matched)
        if self._op == "insert":
            items = self._payload if isinstance(self._payload, list) else [self._payload]
            created = []
            for item in items:
                row = {**item}
                row.setdefault("id", str(uuid.uuid4()))
                row.setdefault("created_at", datetime.now(timezone.utc).isoformat())
                rows.append(row)
                created.append(dict(row))
            return _Result(created)
        if self._op == "update":
            updated = []
            for row in rows:
                if self._matches(row):
                    row.update(self._payload)
                    updated.append(dict(row))
            return _Result(updated)
        raise NotImplementedError(f"FakeSupabase: unsupported op {self._op!r}")


class FakeSupabase:
    def __init__(self):
        self.store: dict[str, list[dict]] = {}

    def table(self, name):
        return _Query(self.store, name)

    def seed(self, table: str, row: dict) -> dict:
        row = dict(row)
        row.setdefault("id", str(uuid.uuid4()))
        row.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        self.store.setdefault(table, []).append(row)
        return row


@pytest.fixture
def fake_db(monkeypatch):
    db = FakeSupabase()
    monkeypatch.setattr("app.routers.brands.get_service_client", lambda: db)
    monkeypatch.setattr("app.routers.campaigns.get_service_client", lambda: db)
    return db


@pytest.fixture
def api_client(fake_db):
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
def login_as():
    def _login(user_id: str) -> None:
        app.dependency_overrides[get_current_user_id] = lambda: user_id

    return _login
