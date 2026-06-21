"""Rider list + manual refresh endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..engine.projection import recompute_projections
from ..models import Rider
from ..schemas import RiderOut

router = APIRouter(prefix="/riders", tags=["riders"])


@router.get("", response_model=list[RiderOut])
def list_riders(db: Session = Depends(get_db)):
    return db.query(Rider).order_by(Rider.star_price.desc()).all()


@router.post("/refresh")
def refresh_projections(db: Session = Depends(get_db)):
    """On-demand refresh button (PRD §8): recompute the expected_points matrix."""
    n = recompute_projections(db)
    return {"recomputed": n}
