"""Deterministic seed data for the demo."""

from __future__ import annotations

import logging
import random
import uuid
from datetime import datetime, timedelta, timezone

from flowdeck.config import get_settings
from flowdeck.db import (
    Record,
    RecordPriority,
    RecordStatus,
    Role,
    User,
    create_all,
    make_engine,
    make_session_factory,
)

log = logging.getLogger(__name__)

QUEUES = ["billing-disputes", "fraud-review", "account-changes", "refunds", "kyc-followups"]
SAMPLE_TITLES = [
    "Duplicate charge on closed card",
    "Customer claims missing refund",
    "Suspicious login from new geo",
    "Address update pending review",
    "Chargeback notice received",
    "Refund request over policy limit",
    "KYC document expired",
    "Account locked after failed verifications",
    "Returned ACH transaction",
    "Manual review for high-risk transfer",
]


def seed(session_factory, *, n: int = 80, seed_value: int = 7) -> None:
    rng = random.Random(seed_value)
    now = datetime.now(timezone.utc)

    with session_factory() as session:
        if session.query(User).count() == 0:
            session.add_all(
                [
                    User(id="u-viewer", email="viewer@flowdeck.test", role=Role.VIEWER),
                    User(id="u-operator", email="operator@flowdeck.test", role=Role.OPERATOR),
                    User(id="u-supervisor", email="supervisor@flowdeck.test", role=Role.SUPERVISOR),
                ]
            )
        if session.query(Record).count() == 0:
            for i in range(n):
                title = rng.choice(SAMPLE_TITLES) + f" #{i + 1:03d}"
                rec = Record(
                    id=f"rec-{i + 1:04d}-{uuid.uuid4().hex[:6]}",
                    title=title,
                    body=f"Auto-generated demo record {i + 1}.",
                    status=rng.choice(list(RecordStatus)),
                    priority=rng.choice(list(RecordPriority)),
                    queue=rng.choice(QUEUES),
                    assignee=rng.choice(["", "", "", "u-operator"]) or None,
                    created_at=now - timedelta(hours=rng.randint(0, 240)),
                    updated_at=now - timedelta(hours=rng.randint(0, 120)),
                    version=1,
                )
                session.add(rec)
        session.commit()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    engine = make_engine(settings.database_url)
    create_all(engine)
    sf = make_session_factory(engine)
    seed(sf)
    log.info("seeded flowdeck demo data")


if __name__ == "__main__":
    main()
