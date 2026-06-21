"""Transfer-planner endpoint (PRD screen: Transfer Planner)."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..engine.transfers import advise_transfer
from ..models import AppState, Stage
from ..schemas import RiderOut, TransferAdvice

router = APIRouter(prefix="/transfers", tags=["transfers"])


def _state_int(db: Session, key: str, default: int) -> int:
    row = db.get(AppState, key)
    return int(row.value) if row and row.value else default


def _state_float(db: Session, key: str, default: float) -> float:
    row = db.get(AppState, key)
    return float(row.value) if row and row.value else default


@router.get("/advice", response_model=TransferAdvice)
def transfer_advice(db: Session = Depends(get_db)):
    transfers_remaining = _state_int(db, "transfers_remaining", 8)
    credits = _state_float(db, "credits", 0.0)
    stages_remaining = (
        db.query(Stage).filter(Stage.date >= date.today()).order_by(Stage.number).all()
    ) or db.query(Stage).order_by(Stage.number).all()

    r = advise_transfer(db, transfers_remaining, credits, stages_remaining)
    return TransferAdvice(
        recommend_transfer=r.recommend,
        rider_out=RiderOut.model_validate(r.rider_out) if r.rider_out else None,
        rider_in=RiderOut.model_validate(r.rider_in) if r.rider_in else None,
        projected_gain=r.projected_gain,
        transfers_remaining=r.transfers_remaining,
        rationale=r.rationale,
    )
