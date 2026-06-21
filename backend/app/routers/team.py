"""My-team state-sync endpoints (PRD screen: My Team).

David manually keeps roster, transfers-used and credits in sync; the engine
reasons from this state.
"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import TOTAL_TRANSFERS
from ..database import get_db
from ..models import AppState, MyTeamRider, Rider
from ..schemas import RiderOut, TeamStateIn

router = APIRouter(prefix="/team", tags=["team"])


def _set_state(db: Session, key: str, value: str) -> None:
    row = db.get(AppState, key)
    if row:
        row.value = value
    else:
        db.add(AppState(key=key, value=value))


@router.get("")
def get_team(db: Session = Depends(get_db)):
    roster_ids = [m.rider_id for m in db.query(MyTeamRider).all()]
    riders = db.query(Rider).filter(Rider.id.in_(roster_ids)).all()
    tr = db.get(AppState, "transfers_remaining")
    cr = db.get(AppState, "credits")
    dm = db.get(AppState, "data_mode")
    return {
        "riders": [RiderOut.model_validate(r) for r in riders],
        "transfers_remaining": int(tr.value) if tr and tr.value else TOTAL_TRANSFERS,
        "credits": float(cr.value) if cr and cr.value else 0.0,
        "data_mode": dm.value if dm else "preview_2025",
    }


@router.put("")
def set_team(payload: TeamStateIn, db: Session = Depends(get_db)):
    db.query(MyTeamRider).delete()
    for rid in payload.rider_ids:
        db.add(MyTeamRider(rider_id=rid, status="equipier", date_added=date.today()))
    _set_state(db, "transfers_remaining", str(TOTAL_TRANSFERS - payload.transfers_used))
    _set_state(db, "credits", str(payload.credits))
    db.commit()
    return get_team(db)
