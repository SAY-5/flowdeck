"""Bidirectional mapping between SQLAlchemy models and protobuf messages."""

from __future__ import annotations

from datetime import UTC, datetime

from flowdeck.db import (
    ActionType as DbAction,
)
from flowdeck.db import (
    AuditEntry,
    Record,
    RecordPriority,
    RecordStatus,
)
from flowdeck.gen import flow_pb2 as pb

_STATUS_TO_PB = {
    RecordStatus.OPEN: pb.RECORD_STATUS_OPEN,
    RecordStatus.IN_PROGRESS: pb.RECORD_STATUS_IN_PROGRESS,
    RecordStatus.RESOLVED: pb.RECORD_STATUS_RESOLVED,
    RecordStatus.REJECTED: pb.RECORD_STATUS_REJECTED,
    RecordStatus.SNOOZED: pb.RECORD_STATUS_SNOOZED,
}
_PB_TO_STATUS = {v: k for k, v in _STATUS_TO_PB.items()}

_PRIORITY_TO_PB = {
    RecordPriority.LOW: pb.RECORD_PRIORITY_LOW,
    RecordPriority.NORMAL: pb.RECORD_PRIORITY_NORMAL,
    RecordPriority.HIGH: pb.RECORD_PRIORITY_HIGH,
    RecordPriority.URGENT: pb.RECORD_PRIORITY_URGENT,
}
_PB_TO_PRIORITY = {v: k for k, v in _PRIORITY_TO_PB.items()}

_ACTION_TO_PB = {
    DbAction.RESOLVE: pb.ACTION_TYPE_RESOLVE,
    DbAction.REJECT: pb.ACTION_TYPE_REJECT,
    DbAction.SNOOZE: pb.ACTION_TYPE_SNOOZE,
    DbAction.REOPEN: pb.ACTION_TYPE_REOPEN,
    DbAction.CLAIM: pb.ACTION_TYPE_CLAIM,
}
_PB_TO_ACTION = {v: k for k, v in _ACTION_TO_PB.items()}


def status_to_pb(status: RecordStatus) -> int:
    return _STATUS_TO_PB[status]


def status_from_pb(value: int) -> RecordStatus:
    return _PB_TO_STATUS[value]


def priority_to_pb(priority: RecordPriority) -> int:
    return _PRIORITY_TO_PB[priority]


def priority_from_pb(value: int) -> RecordPriority:
    return _PB_TO_PRIORITY[value]


def action_to_pb(action: DbAction) -> int:
    return _ACTION_TO_PB[action]


def action_from_pb(value: int) -> DbAction:
    if value not in _PB_TO_ACTION:
        raise ValueError(f"unknown action: {value}")
    return _PB_TO_ACTION[value]


def _rfc3339(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_to_pb(record: Record) -> pb.Record:
    return pb.Record(
        id=record.id,
        title=record.title,
        body=record.body,
        status=status_to_pb(record.status),
        priority=priority_to_pb(record.priority),
        queue=record.queue,
        assignee=record.assignee or "",
        created_at=_rfc3339(record.created_at),
        updated_at=_rfc3339(record.updated_at),
        version=record.version,
    )


def audit_to_pb(entry: AuditEntry) -> pb.AuditEntry:
    return pb.AuditEntry(
        id=entry.id,
        record_id=entry.record_id,
        actor=entry.actor,
        action=action_to_pb(entry.action),
        note=entry.note,
        created_at=_rfc3339(entry.created_at),
    )
