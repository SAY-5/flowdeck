"""Shared test fixtures."""

from __future__ import annotations

import os
from collections.abc import Iterator

import grpc
import pytest
from sqlalchemy import create_engine

from flowdeck.auth import AuthInterceptor, issue_jwt
from flowdeck.db import (
    Base,
    Record,
    RecordPriority,
    RecordStatus,
    Role,
    User,
    make_session_factory,
)
from flowdeck.service import FlowServicer

# Tests can opt into a Postgres container if testcontainers + docker are available.
USE_POSTGRES = os.environ.get("FLOWDECK_TEST_POSTGRES") == "1"

JWT_SECRET = "test-secret-with-at-least-thirty-two-bytes-please"


@pytest.fixture
def engine():
    if USE_POSTGRES:
        from testcontainers.postgres import PostgresContainer

        with PostgresContainer("postgres:16-alpine") as pg:
            url = pg.get_connection_url().replace("postgresql+psycopg2", "postgresql+psycopg")
            eng = create_engine(url, future=True)
            Base.metadata.create_all(eng)
            yield eng
            eng.dispose()
    else:
        eng = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(eng)
        yield eng
        eng.dispose()


@pytest.fixture
def session_factory(engine):
    return make_session_factory(engine)


@pytest.fixture
def seeded(session_factory) -> Iterator[None]:
    with session_factory() as s:
        s.add_all(
            [
                User(id="u-viewer", email="v@x", role=Role.VIEWER),
                User(id="u-operator", email="o@x", role=Role.OPERATOR),
                User(id="u-supervisor", email="s@x", role=Role.SUPERVISOR),
                Record(
                    id="r-1",
                    title="Duplicate charge",
                    body="b",
                    status=RecordStatus.OPEN,
                    priority=RecordPriority.HIGH,
                    queue="billing-disputes",
                ),
                Record(
                    id="r-2",
                    title="Missing refund",
                    body="b",
                    status=RecordStatus.OPEN,
                    priority=RecordPriority.NORMAL,
                    queue="refunds",
                ),
                Record(
                    id="r-3",
                    title="KYC expired",
                    body="b",
                    status=RecordStatus.RESOLVED,
                    priority=RecordPriority.LOW,
                    queue="kyc-followups",
                ),
                Record(
                    id="r-4",
                    title="Suspicious login",
                    body="b",
                    status=RecordStatus.IN_PROGRESS,
                    priority=RecordPriority.URGENT,
                    queue="fraud-review",
                    assignee="u-operator",
                ),
            ]
        )
        s.commit()
    yield


@pytest.fixture
def servicer(session_factory):
    return FlowServicer(session_factory)


@pytest.fixture
def jwt_factory():
    def _make(user_id: str, role: Role) -> str:
        return issue_jwt(user_id, role, JWT_SECRET)

    return _make


@pytest.fixture
def auth_interceptor():
    return AuthInterceptor(secret=JWT_SECRET)


class FakeContext:
    """Minimal stand-in for grpc.ServicerContext used by service tests."""

    def __init__(self, principal=None):
        self.principal = principal
        self.code: grpc.StatusCode | None = None
        self.details: str | None = None
        self.invocation_metadata_value = ()

    def abort(self, code, details):
        self.code = code
        self.details = details
        raise _Abort(code, details)

    def invocation_metadata(self):
        return self.invocation_metadata_value


class _Abort(Exception):
    def __init__(self, code, details):
        self.code = code
        self.details = details
        super().__init__(details)


@pytest.fixture
def fake_context():
    return FakeContext
