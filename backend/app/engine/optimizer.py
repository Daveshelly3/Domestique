"""Initial-squad optimizer (PRD §7 P1) — OR-Tools CP-SAT integer program.

Maximise total season value subject to:
  - budget <= 120 stars
  - exactly 8 riders
  - category caps (leaders<=3, all-rounders<=5, sprinters<=3, climbers<=3)
"""
from __future__ import annotations

from dataclasses import dataclass

from ortools.sat.python import cp_model
from sqlalchemy.orm import Session

from ..config import BUDGET_STARS, CATEGORY_CAPS, SQUAD_SIZE
from ..models import Rider, Stage
from .projection import season_value


@dataclass
class SquadPick:
    rider: Rider
    season_value: float


@dataclass
class SquadResult:
    picks: list[SquadPick]
    total_cost: float
    total_season_value: float
    caps_used: dict[str, int]
    alternatives: list[list[str]]


# Prices are whole/half stars; scale to integers so CP-SAT stays exact.
_PRICE_SCALE = 2


def optimize_initial_squad(db: Session, num_alternatives: int = 2) -> SquadResult:
    riders = db.query(Rider).filter(Rider.status == "active").all()
    stages = db.query(Stage).order_by(Stage.number).all()
    if len(riders) < SQUAD_SIZE:
        raise ValueError("Not enough active riders to build a squad.")

    values = {r.id: season_value(r, stages) for r in riders}
    # CP-SAT objective must be integer; scale values up then divide back.
    _VAL_SCALE = 100

    model = cp_model.CpModel()
    x = {r.id: model.NewBoolVar(f"x_{r.id}") for r in riders}

    model.Add(sum(x.values()) == SQUAD_SIZE)
    model.Add(
        sum(int(round(r.star_price * _PRICE_SCALE)) * x[r.id] for r in riders)
        <= BUDGET_STARS * _PRICE_SCALE
    )
    for archetype, cap in CATEGORY_CAPS.items():
        model.Add(sum(x[r.id] for r in riders if r.archetype == archetype) <= cap)

    model.Maximize(sum(int(round(values[r.id] * _VAL_SCALE)) * x[r.id] for r in riders))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise ValueError("No feasible squad under the given constraints.")

    chosen = [r for r in riders if solver.Value(x[r.id]) == 1]
    chosen.sort(key=lambda r: values[r.id], reverse=True)

    picks = [SquadPick(rider=r, season_value=values[r.id]) for r in chosen]
    caps_used: dict[str, int] = {a: 0 for a in CATEGORY_CAPS}
    for r in chosen:
        caps_used[r.archetype] += 1

    alternatives = _find_alternatives(
        model, solver, x, riders, chosen, num_alternatives
    )

    return SquadResult(
        picks=picks,
        total_cost=round(sum(r.star_price for r in chosen), 1),
        total_season_value=round(sum(values[r.id] for r in chosen), 2),
        caps_used=caps_used,
        alternatives=alternatives,
    )


def _find_alternatives(model, solver, x, riders, chosen, n) -> list[list[str]]:
    """Re-solve with a no-good cut on each prior solution to get ranked alternatives."""
    alts: list[list[str]] = []
    chosen_sets = [chosen]
    for _ in range(n):
        last = chosen_sets[-1]
        # Forbid reproducing the exact previous squad.
        model.Add(sum(x[r.id] for r in last) <= SQUAD_SIZE - 1)
        if solver.Solve(model) not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            break
        alt = [r for r in riders if solver.Value(x[r.id]) == 1]
        chosen_sets.append(alt)
        alts.append([r.name for r in alt])
    return alts
