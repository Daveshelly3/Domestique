"""Seed loader — loads 2026 stages + the 2025 stand-in riders, then computes
the projection matrix. Run with:  python -m app.ingest.seed
"""
from __future__ import annotations

import json
from datetime import date

from sqlalchemy.orm import Session

from ..config import DATA_DIR
from ..database import SessionLocal, init_db
from ..engine.projection import recompute_projections
from ..models import AppState, Rider, Stage


def load_stages(db: Session) -> int:
    with open(DATA_DIR / "stages_2026.json") as f:
        data = json.load(f)
    count = 0
    for s in data["stages"]:
        if db.query(Stage).filter(Stage.number == s["number"]).first():
            continue
        db.add(
            Stage(
                number=s["number"],
                date=date.fromisoformat(s["date"]) if s.get("date") else None,
                type=s["type"],
                distance_km=s["distance_km"],
                climb_points=s["climb_points"],
                is_itt=s["is_itt"],
                is_ttt=s["is_ttt"],
            )
        )
        count += 1
    db.commit()
    return count


def load_riders(db: Session) -> int:
    with open(DATA_DIR / "seed_riders_2025.json") as f:
        data = json.load(f)
    count = 0
    for r in data["riders"]:
        if db.query(Rider).filter(Rider.name == r["name"]).first():
            continue
        db.add(
            Rider(
                name=r["name"],
                team=r["team"],
                archetype=r["archetype"],
                star_price=r["star_price"],
                form=r["form"],
            )
        )
        count += 1
    db.commit()
    return count


def set_state(db: Session, key: str, value: str) -> None:
    row = db.get(AppState, key)
    if row:
        row.value = value
    else:
        db.add(AppState(key=key, value=value))
    db.commit()


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        stages = load_stages(db)
        riders = load_riders(db)
        projections = recompute_projections(db)
        set_state(db, "data_mode", "preview_2025")
        set_state(db, "transfers_remaining", "8")
        set_state(db, "credits", "0")
        print(f"Seeded {stages} stages, {riders} riders, {projections} projections.")
        print("Data mode: Preview - 2025 data")
    finally:
        db.close()


if __name__ == "__main__":
    main()
