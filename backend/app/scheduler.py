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
from .ingest.scraper import StartlistAdapter
from .models import AppState, Stage, PushSubscription
from .notify import send_push


def daily_refresh() -> None:
    db = SessionLocal()
    try:
        adapter = StartlistAdapter()
        if adapter.is_available():
            # TODO: ingest scraped riders/prices here, then flip the badge.
            row = db.get(AppState, "data_mode") or AppState(key="data_mode")
            row.value = "live_2026"
            db.merge(row)
            db.commit()
        n = recompute_projections(db)
        print(f"[scheduler] recomputed {n} projections")  # noqa: T201
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
