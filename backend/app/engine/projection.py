"""Rules-based projection engine (PRD §6 v1).

Produces expected_points[rider][stage]. This is the spine of every
recommendation. v1.1 will swap a gradient-boosted model in behind the same
`project_stage` / `project_all` interface without touching the optimizer.
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from ..config import DATA_DIR
from ..models import Projection, Rider, Stage

with open(DATA_DIR / "scoring_scale.json") as f:
    SCORING = json.load(f)

# Top finish-position points, used to scale a rider's expected finish into points.
_FINISH = SCORING["stage_finish_points"]
_TOP1 = float(_FINISH["1"])

# Archetype suitability per stage type, in [0, 1]. Higher = better fit.
# Rows: stage type -> {archetype: suitability}.
SUITABILITY: dict[str, dict[str, float]] = {
    "flat":     {"sprinter": 1.00, "all_rounder": 0.55, "leader": 0.35, "climber": 0.15},
    "hilly":    {"all_rounder": 1.00, "sprinter": 0.45, "leader": 0.55, "climber": 0.60},
    "mountain": {"climber": 0.95, "leader": 1.00, "all_rounder": 0.40, "sprinter": 0.10},
    "summit":   {"leader": 1.00, "climber": 0.95, "all_rounder": 0.35, "sprinter": 0.05},
    "itt":      {"leader": 1.00, "all_rounder": 0.80, "climber": 0.45, "sprinter": 0.30},
    "ttt":      {"all_rounder": 0.80, "leader": 0.80, "climber": 0.70, "sprinter": 0.70},
    "cobbles":  {"all_rounder": 1.00, "sprinter": 0.55, "leader": 0.45, "climber": 0.25},
}


def project_stage(rider: Rider, stage: Stage) -> float:
    """Expected fantasy points for one rider on one stage.

    expected_points = TOP1 * suitability * form  (+ steady GC accrual for
    leaders + a small TTT split contribution). Deliberately simple and
    transparent; the ML model (v1.1) replaces this function.
    """
    suit = SUITABILITY.get(stage.type, {}).get(rider.archetype, 0.3)
    base = _TOP1 * suit * rider.form

    # GC-classification accrual: only true GC *leaders* bank steady standings
    # points, and chiefly on the stages where the GC is contested (mountains,
    # summit finishes, time trials). Modest per-stage so it complements rather
    # than swamps stage-finish scoring.
    gc_bonus = 0.0
    if rider.archetype == "leader":
        gc_weight = {"summit": 1.0, "mountain": 0.9, "itt": 0.8}.get(stage.type, 0.25)
        gc_bonus = 7.0 * gc_weight * rider.form

    # TTT: each qualified rider gets ~1/8 of the team's placing points (PRD §3).
    # Modelled as a flat split scaled by form; team strength refinement is v1.1.
    ttt_bonus = (_TOP1 / 8.0) * rider.form if stage.is_ttt else 0.0

    return round(base + gc_bonus + ttt_bonus, 2)


def season_value(rider: Rider, stages: list[Stage]) -> float:
    """Sum of expected points over all stages — the optimizer's objective term."""
    return round(sum(project_stage(rider, s) for s in stages), 2)


def recompute_projections(db: Session) -> int:
    """Recompute and persist the full expected_points matrix. Returns row count."""
    riders = db.query(Rider).filter(Rider.status == "active").all()
    stages = db.query(Stage).order_by(Stage.number).all()

    db.query(Projection).delete()
    count = 0
    for rider in riders:
        for stage in stages:
            db.add(
                Projection(
                    rider_id=rider.id,
                    stage_id=stage.id,
                    expected_points=project_stage(rider, stage),
                    model_version=SCORING["model_version"],
                )
            )
            count += 1
    db.commit()
    return count
