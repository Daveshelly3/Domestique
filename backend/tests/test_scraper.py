"""Offline tests for the PCS scraper parsers + live-ingest path.

These run without network access by feeding saved-style HTML to the pure
parser functions and a fake adapter to the ingest function.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.ingest import seed
from app.ingest.scraper import (
    ScrapedRider,
    form_from_results,
    infer_archetype,
    parse_recent_positions,
    parse_startlist,
)
from app.models import Rider

STARTLIST_HTML = """
<ul class="startlist">
  <li class="team">
    <b class="team">UAE Team Emirates</b>
    <ul>
      <li><a href="rider/tadej-pogacar">Tadej Pogacar</a></li>
      <li><a href="rider/joao-almeida">Joao Almeida</a></li>
    </ul>
  </li>
  <li class="team">
    <b class="team">Alpecin-Deceuninck</b>
    <ul>
      <li><a href="rider/jasper-philipsen">Jasper Philipsen</a></li>
    </ul>
  </li>
</ul>
"""

RESULTS_HTML = """
<table><tbody>
  <tr><td>1</td><td>Stage 1</td></tr>
  <tr><td>3</td><td>Stage 2</td></tr>
  <tr><td>DNF</td><td>Stage 3</td></tr>
</tbody></table>
"""


def test_parse_startlist_reads_teams_and_riders():
    riders = parse_startlist(STARTLIST_HTML)
    names = {r.name for r in riders}
    assert names == {"Tadej Pogacar", "Joao Almeida", "Jasper Philipsen"}
    pog = next(r for r in riders if r.name == "Tadej Pogacar")
    assert pog.team == "UAE Team Emirates"


def test_infer_archetype_picks_dominant_speciality():
    assert infer_archetype({"sprint": 200, "gc": 50}) == "sprinter"
    assert infer_archetype({"gc": 300, "climber": 280}) == "leader"
    assert infer_archetype({}) == "all_rounder"


def test_form_from_results():
    positions = parse_recent_positions(RESULTS_HTML, window=10)
    assert positions == [1, 3]  # DNF skipped
    score = form_from_results(positions)
    assert 0.9 < score <= 1.0  # near-podium results -> high form
    assert form_from_results([]) == 0.5


class _FakeAdapter:
    def fetch(self):
        return [
            ScrapedRider(name="Tadej Pogacar", team="UAE", archetype="leader", star_price=30.0, form=0.9),
            ScrapedRider(name="New Rider", team="X", archetype="sprinter", star_price=8.0, form=0.7),
        ]


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine, expire_on_commit=False)()
    seed.load_stages(s)
    seed.load_riders(s)
    yield s
    s.close()


def test_ingest_live_flips_badge_and_upserts(db):
    n = seed.ingest_live_startlist(db, adapter=_FakeAdapter())
    assert n == 2
    from app.models import AppState
    assert db.get(AppState, "data_mode").value == "live_2026"
    # Existing rider updated, new rider inserted.
    assert db.query(Rider).filter(Rider.name == "New Rider").one().archetype == "sprinter"
