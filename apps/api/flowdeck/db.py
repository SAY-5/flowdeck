"""SQLAlchemy schema for FlowDeck."""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class Role(str, enum.Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    SUPERVISOR = "supervisor"


class RecordStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    SNOOZED = "snoozed"


class RecordPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ActionType(str, enum.Enum):
    RESOLVE = "resolve"
    REJECT = "reject"
    SNOOZE = "snooze"
    REOPEN = "reopen"
    CLAIM = "claim"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    role: Mapped[Role] = mapped_column(Enum(Role, name="user_role"), default=Role.VIEWER)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Record(Base):
    __tablename__ = "records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="record_status"), default=RecordStatus.OPEN
    )
    priority: Mapped[RecordPriority] = mapped_column(
        Enum(RecordPriority, name="record_priority"), default=RecordPriority.NORMAL
    )
    queue: Mapped[str] = mapped_column(String(64), index=True)
    assignee: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
    version: Mapped[int] = mapped_column(BigInteger, default=1)

    audit_entries: Mapped[list[AuditEntry]] = relationship(
        back_populates="record", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_records_status_priority", "status", "priority"),
        Index("ix_records_queue_status", "queue", "status"),
    )


class AuditEntry(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    record_id: Mapped[str] = mapped_column(ForeignKey("records.id"), index=True)
    actor: Mapped[str] = mapped_column(String(64))
    action: Mapped[ActionType] = mapped_column(Enum(ActionType, name="action_type"))
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    record: Mapped[Record] = relationship(back_populates="audit_entries")


def make_engine(url: str):
    return create_engine(url, pool_pre_ping=True, future=True)


def make_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def create_all(engine) -> None:
    Base.metadata.create_all(engine)
