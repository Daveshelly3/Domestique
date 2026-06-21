"""Stage + bonus endpoints (PRD screen: Today / Next Stage)."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..engine.bonus import recommend_bonus
from ..models import Stage
from ..schemas import BonusRecommendation, StageOut

router = APIRouter(prefix="/stages", tags=["stages"])


@router.get("", response_model=list[StageOut])
def list_stages(db: Session = Depends(get_db)):
    return db.query(Stage).order_by(Stage.number).all()


@router.get("/next", response_model=StageOut)
def next_stage(db: Session = Depends(get_db)):
    today = date.today()
    stage = (
        db.query(Stage)
        .filter(Stage.date >= today)
        .order_by(Stage.number)
        .first()
    ) or db.query(Stage).order_by(Stage.number).first()
    if not stage:
        raise HTTPException(404, "No stages loaded.")
    return stage


@router.get("/{number}/bonus", response_model=BonusRecommendation)
def bonus_for_stage(number: int, db: Session = Depends(get_db)):
    stage = db.query(Stage).filter(Stage.number == number).first()
    if not stage:
        raise HTTPException(404, "Stage not found.")
    result = recommend_bonus(db, stage)
    return BonusRecommendation(
        stage_number=stage.number,
        bonus_rider=result.bonus_rider,
        marginal_doubled_points=result.marginal_doubled_points,
        equipiers=result.equipiers,
    )
