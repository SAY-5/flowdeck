"""Integration tests against a real Postgres via testcontainers.

Skipped by default; enable with FLOWDECK_TEST_POSTGRES=1 and a docker daemon.
"""

from __future__ import annotations

import os
import shutil

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("FLOWDECK_TEST_POSTGRES") != "1" or shutil.which("docker") is None,
    reason="set FLOWDECK_TEST_POSTGRES=1 and have docker installed to run",
)


def test_full_lifecycle_against_postgres(servicer, seeded, fake_context):
    from flowdeck.auth import Principal
    from flowdeck.db import Role
    from flowdeck.gen import flow_pb2 as pb

    op = Principal(user_id="u-op", role=Role.OPERATOR)
    ctx = fake_context(principal=op)

    resp = servicer.ListRecords(pb.ListRecordsRequest(status=[pb.RECORD_STATUS_OPEN]), ctx)
    assert resp.total >= 1

    record = resp.records[0]
    act_resp = servicer.ActOnRecord(
        pb.ActOnRecordRequest(
            id=record.id,
            action=pb.ACTION_TYPE_RESOLVE,
            expected_version=record.version,
            note="pg-integration",
        ),
        ctx,
    )
    assert act_resp.record.status == pb.RECORD_STATUS_RESOLVED
    assert act_resp.record.version == record.version + 1

    audit = servicer.ListAuditLog(pb.ListAuditLogRequest(record_id=record.id), ctx)
    assert len(audit.entries) >= 1
