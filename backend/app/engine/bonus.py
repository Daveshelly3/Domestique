"""Daily Stage-Winner-Bonus + status picker (PRD §7 P2).

Given the current roster and a stage, pick the rider whose doubled points add
the most marginal value, and assign the other 7 as equipiers.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..models import MyTeamRider, Rider, Stage
from .projection import project_stage


@dataclass
class BonusResult:
    stage: Stage
    bonus_rider: Rider | None
    marginal_doubled_points: float
    equipiers: list[Rider]


def recommend_bonus(db: Session, stage: Stage) -> BonusResult:
    roster_ids = [m.rider_id for m in db.query(MyTeamRider).all()]
    roster = db.query(Rider).filter(Rider.id.in_(roster_ids)).all()
    if not roster:
        return BonusResult(stage=stage, bonus_rider=None, marginal_doubled_points=0.0, equipiers=[])

    # Marginal gain from bonus = the rider's own expected points (doubling adds
    # one extra copy). Pick the max-projection rider for this stage.
    scored = sorted(roster, key=lambda r: project_stage(r, stage), reverse=True)
    bonus = scored[0]
    return BonusResult(
        stage=stage,
        bonus_rider=bonus,
        marginal_doubled_points=round(project_stage(bonus, stage), 2),
        equipiers=scored[1:],
    )
