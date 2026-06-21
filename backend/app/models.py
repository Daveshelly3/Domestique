"""ORM models — mirrors the PRD §11 data model."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Rider(Base):
    __tablename__ = "riders"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)
    team: Mapped[str] = mapped_column(String, default="")
    archetype: Mapped[str] = mapped_column(String)  # leader|all_rounder|sprinter|climber
    star_price: Mapped[float] = mapped_column(Float, default=0.0)
    form: Mapped[float] = mapped_column(Float, default=0.5)  # 0..1 trailing-form score
    status: Mapped[str] = mapped_column(String, default="active")  # active|abandoned

    projections: Mapped[list["Projection"]] = relationship(back_populates="rider")


class Stage(Base):
    __tablename__ = "stages"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    type: Mapped[str] = mapped_column(String)  # flat|hilly|mountain|summit|itt|ttt|cobbles
    distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    climb_points: Mapped[int] = mapped_column(Integer, default=0)  # weighted categorised-climb score
    is_itt: Mapped[bool] = mapped_column(Boolean, default=False)
    is_ttt: Mapped[bool] = mapped_column(Boolean, default=False)


class Result(Base):
    __tablename__ = "results"
    __table_args__ = (UniqueConstraint("rider_id", "stage_id", name="uq_result_rider_stage"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    rider_id: Mapped[int] = mapped_column(ForeignKey("riders.id"))
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id"))
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    breakaway_km: Mapped[float] = mapped_column(Float, default=0.0)
    fantasy_points: Mapped[float | None] = mapped_column(Float, nullable=True)


class Projection(Base):
    __tablename__ = "projections"
    __table_args__ = (UniqueConstraint("rider_id", "stage_id", name="uq_proj_rider_stage"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    rider_id: Mapped[int] = mapped_column(ForeignKey("riders.id"))
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id"))
    expected_points: Mapped[float] = mapped_column(Float, default=0.0)
    model_version: Mapped[str] = mapped_column(String, default="rules-v1")

    rider: Mapped["Rider"] = relationship(back_populates="projections")


class MyTeamRider(Base):
    __tablename__ = "my_team"

    id: Mapped[int] = mapped_column(primary_key=True)
    rider_id: Mapped[int] = mapped_column(ForeignKey("riders.id"), unique=True)
    status: Mapped[str] = mapped_column(String, default="equipier")  # bonus|equipier
    date_added: Mapped[date | None] = mapped_column(Date, nullable=True)


class Transfer(Base):
    __tablename__ = "transfers"

    id: Mapped[int] = mapped_column(primary_key=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id"))
    rider_out: Mapped[int] = mapped_column(ForeignKey("riders.id"))
    rider_in: Mapped[int] = mapped_column(ForeignKey("riders.id"))
    credits_delta: Mapped[float] = mapped_column(Float, default=0.0)
    transfers_remaining: Mapped[int] = mapped_column(Integer, default=0)


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint: Mapped[str] = mapped_column(String, unique=True)
    p256dh: Mapped[str] = mapped_column(String)
    auth: Mapped[str] = mapped_column(String)


class AppState(Base):
    """Single-row key/value store (data-readiness badge, transfers left, credits)."""

    __tablename__ = "app_state"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(String, default="")
