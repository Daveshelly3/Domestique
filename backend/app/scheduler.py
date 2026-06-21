"""Daily refresh + deadline-push job (PRD §5, §10).

Run alongside the API (Railway/Render cron or APScheduler). Each day it:
  1. polls the startlist adapter; ingests + flips badge to '2026 Live' on publish
  2. refreshes form, recomputes the projection matrix
  3. queues deadline pushes for the next stage (configurable lead time)

This is a scaffold — wire the real adapter parsing in app/ingest/scraper.py.
"""
from __future__ import annotations

from datetime import date

from apscheduler.schedulers.blocking import BlockingScheduler

from .database import SessionLocal
from .engine.projection import recompute_projections
from .ingest.seed import ingest_live_startlist
from .models import Stage, PushSubscription
from .notify import send_push


def daily_refresh() -> None:
    db = SessionLocal()
    try:
        # Poll for the real 2026 startlist; on publish this ingests + flips the
        # badge to '2026 Live' and recomputes. Returns 0 while still in Preview.
        ingested = ingest_live_startlist(db)
        if ingested:
            print(f"[scheduler] ingested {ingested} riders -> 2026 Live")  # noqa: T201
        else:
            recompute_projections(db)  # keep Preview projections fresh
        _queue_deadline_pushes(db)
    finally:
        db.close()


def _queue_deadline_pushes(db) -> None:
    stage = (
        db.query(Stage).filter(Stage.date >= date.today()).order_by(Stage.number).first()
    )
    if not stage:
        return
    subs = db.query(PushSubscription).all()
    for s in subs:
        send_push(
            {"endpoint": s.endpoint, "keys": {"p256dh": s.p256dh, "auth": s.auth}},
            title=f"Stage {stage.number} deadline soon",
            body="Set your bonus pick and check transfer advice in Domestique.",
        )


def main() -> None:
    sched = BlockingScheduler(timezone="UTC")
    # Daily at 06:00 UTC (08:00 CEST/SAST — both UTC+2 in July).
    sched.add_job(daily_refresh, "cron", hour=6, minute=0)
    print("[scheduler] started; daily refresh at 06:00 UTC")  # noqa: T201
    sched.start()


if __name__ == "__main__":
    main()
