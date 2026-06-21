"""End-to-end test of the projection + optimizer pipeline on seed data."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import BUDGET_STARS, CATEGORY_CAPS, SQUAD_SIZE
from app.database import Base
from app.engine.optimizer import optimize_initial_squad
from app.engine.projection import recompute_projections
from app.ingest import seed


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    s = Session()
    seed.load_stages(s)
    seed.load_riders(s)
    recompute_projections(s)
    yield s
    s.close()


def test_squad_respects_constraints(db):
    result = optimize_initial_squad(db)
    assert len(result.picks) == SQUAD_SIZE
    assert result.total_cost <= BUDGET_STARS
    for archetype, cap in CATEGORY_CAPS.items():
        assert result.caps_used.get(archetype, 0) <= cap


def test_squad_is_nonempty_and_valued(db):
    result = optimize_initial_squad(db)
    assert result.total_season_value > 0
    assert len(result.alternatives) >= 1
