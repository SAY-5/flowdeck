"""Unit tests for FlowServicer."""

from __future__ import annotations

import pytest

from flowdeck.auth import Principal
from flowdeck.db import Role
from flowdeck.gen import flow_pb2 as pb


def _principal(role: Role = Role.OPERATOR, user_id: str = "u-op") -> Principal:
    return Principal(user_id=user_id, role=role)


def test_list_records_returns_all_when_unfiltered(servicer, seeded, fake_context):
    ctx = fake_context()
    resp = servicer.ListRecords(pb.ListRecordsRequest(), ctx)
    assert resp.total == 4
    assert len(resp.records) == 4
    ids = sorted(r.id for r in resp.records)
    assert ids == ["r-1", "r-2", "r-3", "r-4"]


def test_list_records_filters_by_status(servicer, seeded, fake_context):
    ctx = fake_context()
    req = pb.ListRecordsRequest(status=[pb.RECORD_STATUS_OPEN])
    resp = servicer.ListRecords(req, ctx)
    assert {r.id for r in resp.records} == {"r-1", "r-2"}
    assert resp.total == 2


def test_list_records_filters_by_search(servicer, seeded, fake_context):
    ctx = fake_context()
    resp = servicer.ListRecords(pb.ListRecordsRequest(search="refund"), ctx)
    assert {r.id for r in resp.records} == {"r-2"}


def test_facets_reflect_other_dimensions(servicer, seeded, fake_context):
    """When filtering by status=open, the status facet still shows resolved count."""
    ctx = fake_context()
    req = pb.ListRecordsRequest(status=[pb.RECORD_STATUS_OPEN])
    resp = servicer.ListRecords(req, ctx)
    by_status = {b.value: b.count for b in resp.facets.status}
    # The OPEN filter should NOT collapse the status facet to only OPEN.
    assert by_status["open"] == 2
    assert by_status["resolved"] == 1


def test_get_record_404(servicer, seeded, fake_context):
    import grpc

    ctx = fake_context()
    with pytest.raises(Exception):
        servicer.GetRecord(pb.GetRecordRequest(id="nope"), ctx)
    assert ctx.code == grpc.StatusCode.NOT_FOUND


def test_act_on_record_resolves_and_bumps_version(servicer, seeded, fake_context):
    ctx = fake_context(principal=_principal(Role.OPERATOR))
    resp = servicer.ActOnRecord(
        pb.ActOnRecordRequest(id="r-1", action=pb.ACTION_TYPE_RESOLVE, note="done"),
        ctx,
    )
    assert resp.record.status == pb.RECORD_STATUS_RESOLVED
    assert resp.record.version == 2


def test_act_on_record_claim_assigns(servicer, seeded, fake_context):
    ctx = fake_context(principal=_principal(Role.OPERATOR, user_id="u-claim"))
    resp = servicer.ActOnRecord(
        pb.ActOnRecordRequest(id="r-2", action=pb.ACTION_TYPE_CLAIM),
        ctx,
    )
    assert resp.record.assignee == "u-claim"
    assert resp.record.status == pb.RECORD_STATUS_IN_PROGRESS


def test_act_on_record_reopen_requires_supervisor(servicer, seeded, fake_context):
    import grpc

    ctx = fake_context(principal=_principal(Role.OPERATOR))
    with pytest.raises(Exception):
        servicer.ActOnRecord(
            pb.ActOnRecordRequest(id="r-3", action=pb.ACTION_TYPE_REOPEN),
            ctx,
        )
    assert ctx.code == grpc.StatusCode.PERMISSION_DENIED


def test_act_on_record_reopen_works_for_supervisor(servicer, seeded, fake_context):
    ctx = fake_context(principal=_principal(Role.SUPERVISOR, user_id="u-sup"))
    resp = servicer.ActOnRecord(
        pb.ActOnRecordRequest(id="r-3", action=pb.ACTION_TYPE_REOPEN, note="ok"),
        ctx,
    )
    assert resp.record.status == pb.RECORD_STATUS_OPEN


def test_act_on_record_version_mismatch(servicer, seeded, fake_context):
    import grpc

    ctx = fake_context(principal=_principal(Role.OPERATOR))
    with pytest.raises(Exception):
        servicer.ActOnRecord(
            pb.ActOnRecordRequest(id="r-1", action=pb.ACTION_TYPE_RESOLVE, expected_version=99),
            ctx,
        )
    assert ctx.code == grpc.StatusCode.FAILED_PRECONDITION


def test_audit_log_records_action(servicer, seeded, fake_context):
    ctx_op = fake_context(principal=_principal(Role.OPERATOR, user_id="u-actor"))
    servicer.ActOnRecord(
        pb.ActOnRecordRequest(id="r-2", action=pb.ACTION_TYPE_RESOLVE, note="approved"),
        ctx_op,
    )
    ctx_view = fake_context()
    log = servicer.ListAuditLog(pb.ListAuditLogRequest(record_id="r-2"), ctx_view)
    assert len(log.entries) == 1
    entry = log.entries[0]
    assert entry.actor == "u-actor"
    assert entry.action == pb.ACTION_TYPE_RESOLVE
    assert entry.note == "approved"


def test_pagination_cursor(servicer, seeded, fake_context):
    ctx = fake_context()
    resp1 = servicer.ListRecords(pb.ListRecordsRequest(page_size=2), ctx)
    assert len(resp1.records) == 2
    assert resp1.next_page_token != ""
    resp2 = servicer.ListRecords(
        pb.ListRecordsRequest(page_size=2, page_token=resp1.next_page_token), ctx
    )
    assert len(resp2.records) == 2
    page1_ids = {r.id for r in resp1.records}
    page2_ids = {r.id for r in resp2.records}
    assert page1_ids.isdisjoint(page2_ids)


def test_get_facets_no_filter(servicer, seeded, fake_context):
    ctx = fake_context()
    resp = servicer.GetFacets(pb.GetFacetsRequest(), ctx)
    by_status = {b.value: b.count for b in resp.status}
    assert by_status == {"open": 2, "in_progress": 1, "resolved": 1}
