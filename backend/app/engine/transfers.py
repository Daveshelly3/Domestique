"""Transfer-timing planner (PRD §7 P3) — v1 heuristic.

Trigger a transfer only when the projected gain over the remaining stages
exceeds a threshold AND budget allows, while reserving transfers for likely
abandons. v1.1 upgrades this to a rollout/DP over the remaining schedule.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..models import MyTeamRider, Rider, Stage
from .projection import season_value

# Minimum projected season-point gain to justify burning a transfer.
GAIN_THRESHOLD = 25.0
# Keep this many transfers in reserve for abandons until late in the race.
ABANDON_RESERVE = 2


@dataclass
class TransferAdviceResult:
    recommend: bool
    rider_out: Rider | None = None
    rider_in: Rider | None = None
    projected_gain: float = 0.0
    transfers_remaining: int = 0
    rationale: str = ""


def advise_transfer(
    db: Session,
    transfers_remaining: int,
    credits: float,
    stages_remaining: list[Stage],
) -> TransferAdviceResult:
    roster_ids = [m.rider_id for m in db.query(MyTeamRider).all()]
    roster = db.query(Rider).filter(Rider.id.in_(roster_ids)).all()
    if not roster or transfers_remaining <= 0 or not stages_remaining:
        return TransferAdviceResult(
            recommend=False,
            transfers_remaining=transfers_remaining,
            rationale="No roster, no transfers left, or season over.",
        )

    market = (
        db.query(Rider)
        .filter(Rider.status == "active", Rider.id.notin_(roster_ids))
        .all()
    )

    best = None  # (gain, out_rider, in_rider)
    for out_r in roster:
        out_val = season_value(out_r, stages_remaining)
        # A replacement must fit within freed budget: price_in <= price_out + credits.
        budget_for_in = out_r.star_price + credits
        for in_r in market:
            if in_r.archetype != out_r.archetype:
                continue  # keep category caps trivially satisfied
            if in_r.star_price > budget_for_in:
                continue
            gain = season_value(in_r, stages_remaining) - out_val
            if best is None or gain > best[0]:
                best = (gain, out_r, in_r)

    if best is None:
        return TransferAdviceResult(
            recommend=False,
            transfers_remaining=transfers_remaining,
            rationale="No affordable, cap-compatible upgrade available.",
        )

    gain, out_r, in_r = best
    spendable = transfers_remaining - ABANDON_RESERVE
    # Late in the race the reserve relaxes (fewer stages where abandons matter).
    if len(stages_remaining) <= 5:
        spendable = transfers_remaining

    recommend = gain >= GAIN_THRESHOLD and spendable > 0
    if recommend:
        rationale = (
            f"Swap {out_r.name} -> {in_r.name} projects +{gain:.0f} pts over the "
            f"remaining {len(stages_remaining)} stages, above the {GAIN_THRESHOLD:.0f} "
            f"threshold, with {transfers_remaining} transfers in hand."
        )
    else:
        why = []
        if gain < GAIN_THRESHOLD:
            why.append(f"best gain +{gain:.0f} < {GAIN_THRESHOLD:.0f} threshold")
        if spendable <= 0:
            why.append(f"holding {ABANDON_RESERVE} transfers in reserve for abandons")
        rationale = "Hold: " + "; ".join(why) + "."

    return TransferAdviceResult(
        recommend=recommend,
        rider_out=out_r,
        rider_in=in_r,
        projected_gain=round(gain, 1),
        transfers_remaining=transfers_remaining,
        rationale=rationale,
    )
