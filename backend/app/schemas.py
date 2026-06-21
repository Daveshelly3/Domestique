"""Pydantic response/request schemas."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class RiderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    team: str
    archetype: str
    star_price: float
    form: float
    status: str


class StageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    number: int
    date: date | None
    start_time: datetime | None
    type: str
    distance_km: float
    climb_points: int
    is_itt: bool
    is_ttt: bool


class SquadRider(BaseModel):
    rider: RiderOut
    season_value: float
    reason: str


class SquadRecommendation(BaseModel):
    riders: list[SquadRider]
    total_cost: float
    total_season_value: float
    budget: float
    caps_used: dict[str, int]
    alternatives: list[list[str]] = []


class BonusRecommendation(BaseModel):
    stage_number: int
    bonus_rider: RiderOut | None
    marginal_doubled_points: float
    equipiers: list[RiderOut]


class TransferAdvice(BaseModel):
    recommend_transfer: bool
    rider_out: RiderOut | None = None
    rider_in: RiderOut | None = None
    projected_gain: float = 0.0
    transfers_remaining: int = 0
    rationale: str = ""


class TeamStateIn(BaseModel):
    rider_ids: list[int]
    transfers_used: int = 0
    credits: float = 0.0


class PushSubscriptionIn(BaseModel):
    endpoint: str
    keys: dict[str, str]
