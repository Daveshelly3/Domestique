"""Initial-squad recommendation endpoint (PRD screen: Squad Builder)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import BUDGET_STARS
from ..database import get_db
from ..engine.optimizer import optimize_initial_squad
from ..schemas import RiderOut, SquadRecommendation, SquadRider

router = APIRouter(prefix="/squad", tags=["squad"])

_REASON = {
    "leader": "GC engine — steady classification points + mountain upside.",
    "all_rounder": "Versatile scorer across hilly/flat stages; bonus-pick flexibility.",
    "sprinter": "Flat-stage points magnet; high ceiling on bunch finishes.",
    "climber": "Cheap mountain points; summit-finish breakaway upside.",
}


@router.get("/recommend", response_model=SquadRecommendation)
def recommend_squad(db: Session = Depends(get_db)):
    try:
        result = optimize_initial_squad(db)
    except ValueError as e:
        raise HTTPException(409, str(e))

    riders = [
        SquadRider(
            rider=RiderOut.model_validate(p.rider),
            season_value=p.season_value,
            reason=_REASON.get(p.rider.archetype, ""),
        )
        for p in result.picks
    ]
    return SquadRecommendation(
        riders=riders,
        total_cost=result.total_cost,
        total_season_value=result.total_season_value,
        budget=float(BUDGET_STARS),
        caps_used=result.caps_used,
        alternatives=result.alternatives,
    )
