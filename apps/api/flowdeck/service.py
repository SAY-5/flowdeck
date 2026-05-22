"""FlowService implementation."""

from __future__ import annotations

import base64
import uuid
from collections.abc import Callable
from datetime import datetime, timezone

import grpc
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from flowdeck.auth import ACTION_ROLE_OVERRIDES, role_satisfies
from flowdeck.db import (
    ActionType as DbAction,
)
from flowdeck.db import (
    AuditEntry,
    Record,
    RecordPriority,
    RecordStatus,
    Role,
)
from flowdeck.gen import flow_pb2 as pb
from flowdeck.gen import flow_pb2_grpc as pb_grpc
from flowdeck.mapping import (
    action_from_pb,
    action_to_pb,
    audit_to_pb,
    priority_from_pb,
    priority_to_pb,
    record_to_pb,
    status_from_pb,
    status_to_pb,
)


# Action -> resulting status. None means "do not change status".
_ACTION_TRANSITIONS: dict[DbAction, RecordStatus | None] = {
    DbAction.RESOLVE: RecordStatus.RESOLVED,
    DbAction.REJECT: RecordStatus.REJECTED,
    DbAction.SNOOZE: RecordStatus.SNOOZED,
    DbAction.REOPEN: RecordStatus.OPEN,
    DbAction.CLAIM: RecordStatus.IN_PROGRESS,
}


def _encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(str(offset).encode()).decode().rstrip("=")


def _decode_cursor(token: str) -> int:
    if not token:
        return 0
    padded = token + "=" * (-len(token) % 4)
    try:
        return int(base64.urlsafe_b64decode(padded).decode())
    except (ValueError, UnicodeDecodeError):
        return 0


class FlowServicer(pb_grpc.FlowServiceServicer):
    """Concrete gRPC service. Constructed with a session factory."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        page_size_default: int = 50,
        page_size_max: int = 200,
    ) -> None:
        self._sf = session_factory
        self._clock = clock
        self._page_size_default = page_size_default
        self._page_size_max = page_size_max

    # ----- ListRecords -----

    def ListRecords(self, request: pb.ListRecordsRequest, context) -> pb.ListRecordsResponse:
        size = self._clamp_size(request.page_size)
        offset = _decode_cursor(request.page_token)

        with self._sf() as session:
            stmt = self._apply_filters(select(Record), request)
            stmt = stmt.order_by(Record.created_at.desc(), Record.id.desc())

            total = session.scalar(self._apply_filters(select(func.count(Record.id)), request)) or 0
            rows = list(session.scalars(stmt.offset(offset).limit(size + 1)))
            has_more = len(rows) > size
            rows = rows[:size]

            facets = self._compute_facets(
                session,
                statuses=list(request.status),
                priorities=list(request.priority),
                queues=list(request.queue),
                search=request.search,
            )

            return pb.ListRecordsResponse(
                records=[record_to_pb(r) for r in rows],
                next_page_token=_encode_cursor(offset + size) if has_more else "",
                total=total,
                facets=facets,
            )

    # ----- GetRecord -----

    def GetRecord(self, request: pb.GetRecordRequest, context) -> pb.Record:
        with self._sf() as session:
            row = session.get(Record, request.id)
            if row is None:
                context.abort(grpc.StatusCode.NOT_FOUND, f"record not found: {request.id}")
            return record_to_pb(row)

    # ----- ActOnRecord -----

    def ActOnRecord(self, request: pb.ActOnRecordRequest, context) -> pb.ActOnRecordResponse:
        principal = getattr(context, "principal", None)
        if principal is None:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "no principal on context")

        try:
            action = action_from_pb(request.action)
        except ValueError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))

        override_role_name = ACTION_ROLE_OVERRIDES.get(pb.ActionType.Name(request.action))
        if override_role_name and not role_satisfies(principal.role, override_role_name):
            context.abort(
                grpc.StatusCode.PERMISSION_DENIED,
                f"action {action.value} requires role {override_role_name.value}",
            )

        with self._sf() as session:
            row = session.get(Record, request.id)
            if row is None:
                context.abort(grpc.StatusCode.NOT_FOUND, f"record not found: {request.id}")
            if request.expected_version and row.version != request.expected_version:
                context.abort(
                    grpc.StatusCode.FAILED_PRECONDITION,
                    f"version mismatch: server={row.version}, client={request.expected_version}",
                )

            new_status = _ACTION_TRANSITIONS.get(action)
            if new_status is not None:
                row.status = new_status
            if action == DbAction.CLAIM:
                row.assignee = principal.user_id

            row.version += 1
            row.updated_at = self._clock()

            entry = AuditEntry(
                id=str(uuid.uuid4()),
                record_id=row.id,
                actor=principal.user_id,
                action=action,
                note=request.note,
                created_at=self._clock(),
            )
            session.add(entry)
            session.commit()
            session.refresh(row)

            return pb.ActOnRecordResponse(record=record_to_pb(row))

    # ----- GetFacets -----

    def GetFacets(self, request: pb.GetFacetsRequest, context) -> pb.FacetCounts:
        with self._sf() as session:
            return self._compute_facets(
                session,
                statuses=list(request.status),
                priorities=list(request.priority),
                queues=list(request.queue),
                search=request.search,
            )

    # ----- ListAuditLog -----

    def ListAuditLog(self, request: pb.ListAuditLogRequest, context) -> pb.ListAuditLogResponse:
        size = self._clamp_size(request.page_size)
        offset = _decode_cursor(request.page_token)
        with self._sf() as session:
            stmt = (
                select(AuditEntry)
                .where(AuditEntry.record_id == request.record_id)
                .order_by(AuditEntry.created_at.desc(), AuditEntry.id.desc())
                .offset(offset)
                .limit(size + 1)
            )
            rows = list(session.scalars(stmt))
            has_more = len(rows) > size
            rows = rows[:size]
            return pb.ListAuditLogResponse(
                entries=[audit_to_pb(r) for r in rows],
                next_page_token=_encode_cursor(offset + size) if has_more else "",
            )

    # ----- helpers -----

    def _clamp_size(self, requested: int) -> int:
        if requested <= 0:
            return self._page_size_default
        return min(requested, self._page_size_max)

    def _apply_filters(self, stmt, request):
        if request.status:
            stmt = stmt.where(Record.status.in_([status_from_pb(s) for s in request.status]))
        if request.priority:
            stmt = stmt.where(Record.priority.in_([priority_from_pb(p) for p in request.priority]))
        if request.queue:
            stmt = stmt.where(Record.queue.in_(list(request.queue)))
        if getattr(request, "assignee", ""):
            stmt = stmt.where(Record.assignee == request.assignee)
        if getattr(request, "search", ""):
            needle = f"%{request.search.lower()}%"
            stmt = stmt.where(func.lower(Record.title).like(needle))
        return stmt

    def _compute_facets(
        self,
        session: Session,
        *,
        statuses: list[int],
        priorities: list[int],
        queues: list[str],
        search: str,
    ) -> pb.FacetCounts:
        # Facets are computed BEFORE filtering on that facet's dimension.
        # So a click on "status=open" still shows you the other status counts.
        # This is the classic ecommerce facet behavior.
        base_filters = {
            "status": [status_from_pb(s) for s in statuses],
            "priority": [priority_from_pb(p) for p in priorities],
            "queue": list(queues),
            "search": search,
        }

        def apply(stmt, exclude: str):
            if exclude != "status" and base_filters["status"]:
                stmt = stmt.where(Record.status.in_(base_filters["status"]))
            if exclude != "priority" and base_filters["priority"]:
                stmt = stmt.where(Record.priority.in_(base_filters["priority"]))
            if exclude != "queue" and base_filters["queue"]:
                stmt = stmt.where(Record.queue.in_(base_filters["queue"]))
            if base_filters["search"]:
                needle = f"%{base_filters['search'].lower()}%"
                stmt = stmt.where(func.lower(Record.title).like(needle))
            return stmt

        status_rows = session.execute(
            apply(select(Record.status, func.count()).group_by(Record.status), "status")
        ).all()
        priority_rows = session.execute(
            apply(select(Record.priority, func.count()).group_by(Record.priority), "priority")
        ).all()
        queue_rows = session.execute(
            apply(select(Record.queue, func.count()).group_by(Record.queue), "queue")
        ).all()

        return pb.FacetCounts(
            status=[
                pb.FacetBucket(value=RecordStatus(s).value if isinstance(s, RecordStatus) else str(s), count=c)
                for s, c in status_rows
            ],
            priority=[
                pb.FacetBucket(
                    value=RecordPriority(p).value if isinstance(p, RecordPriority) else str(p),
                    count=c,
                )
                for p, c in priority_rows
            ],
            queue=[pb.FacetBucket(value=q, count=c) for q, c in queue_rows],
        )


# Re-export for tests that want to bypass facet dimension keys.
__all__ = ["FlowServicer", "Role", "status_to_pb", "priority_to_pb", "action_to_pb"]
