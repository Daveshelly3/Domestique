"""Scraper adapter layer (PRD §8).

A thin adapter so a source change (PCS / FirstCycling / ASO) doesn't ripple into
the engine. Callers depend only on `StartlistAdapter.fetch()` and
`FormAdapter.fetch_form()`; the HTTP + parsing lives here.

Hygiene (PRD §8): a descriptive User-Agent, polite rate-limiting between
requests, and aggressive on-disk caching so repeated daily runs don't re-hit the
source. Single-user, personal use.

Network note: ProCyclingStats provides the startlist (names, teams) and results
(for form). The Tissot **star prices** come from the in-game data and are merged
in separately once published; until then prices default to 0 and the app stays
in 'Preview - 2025 data' mode.
"""
from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

PCS_BASE = "https://www.procyclingstats.com"
USER_AGENT = "Domestique/0.1 (personal TdF-fantasy helper; single-user)"
CACHE_DIR = Path(__file__).parent.parent / ".cache"
CACHE_TTL_SECONDS = 6 * 60 * 60  # 6h — daily refresh re-uses within a session
RATE_LIMIT_SECONDS = 2.0  # polite delay between live requests


@dataclass
class ScrapedRider:
    name: str
    team: str
    archetype: str = "all_rounder"
    star_price: float = 0.0
    form: float = 0.5


# --- HTTP client with cache + rate-limit ---------------------------------

class PCSClient:
    def __init__(self, *, cache_dir: Path = CACHE_DIR, ttl: int = CACHE_TTL_SECONDS):
        self.cache_dir = cache_dir
        self.ttl = ttl
        self._last_request = 0.0
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, url: str) -> Path:
        return self.cache_dir / (hashlib.sha256(url.encode()).hexdigest() + ".html")

    def get(self, url: str) -> str:
        cached = self._cache_path(url)
        if cached.exists() and (time.time() - cached.stat().st_mtime) < self.ttl:
            return cached.read_text(encoding="utf-8")

        # Polite rate-limit between live fetches.
        wait = RATE_LIMIT_SECONDS - (time.time() - self._last_request)
        if wait > 0:
            time.sleep(wait)

        resp = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=20.0, follow_redirects=True)
        self._last_request = time.time()
        resp.raise_for_status()
        cached.write_text(resp.text, encoding="utf-8")
        return resp.text


# --- Archetype inference --------------------------------------------------

# PCS rider pages expose "speciality" points (sprint / climber / gc / one-day-races
# / time-trial). We map the dominant speciality to our four archetypes.
_SPECIALITY_TO_ARCHETYPE = {
    "sprint": "sprinter",
    "climber": "climber",
    "gc": "leader",
    "time_trial": "leader",
    "one_day_races": "all_rounder",
    "hills": "all_rounder",
}


def infer_archetype(speciality_points: dict[str, float]) -> str:
    """Pick the archetype from a rider's dominant PCS speciality. Defaults to all-rounder."""
    if not speciality_points:
        return "all_rounder"
    top = max(speciality_points, key=speciality_points.get)
    return _SPECIALITY_TO_ARCHETYPE.get(top, "all_rounder")


# --- Parsers (pure functions over HTML, so they're testable offline) ------

_RIDER_HREF = re.compile(r"^rider/[a-z0-9\-]+$", re.I)


def parse_startlist(html: str) -> list[ScrapedRider]:
    """Parse a PCS race startlist page into riders.

    Tolerant to PCS markup drift: walks each team block, reads the team name
    and the rider links within it. Riders with no resolvable team still parse.
    """
    soup = BeautifulSoup(html, "html.parser")
    riders: list[ScrapedRider] = []
    seen: set[str] = set()

    for team_li in soup.select("li.team, div.team"):
        team_name_el = team_li.select_one("b.team, a.team, .team-name")
        team_name = team_name_el.get_text(strip=True) if team_name_el else ""
        for a in team_li.find_all("a", href=_RIDER_HREF):
            name = a.get_text(strip=True)
            if not name or name in seen:
                continue
            seen.add(name)
            riders.append(ScrapedRider(name=name, team=team_name))

    # Fallback: some startlist layouts list riders flat, not nested in teams.
    if not riders:
        for a in soup.find_all("a", href=_RIDER_HREF):
            name = a.get_text(strip=True)
            if name and name not in seen:
                seen.add(name)
                riders.append(ScrapedRider(name=name, team=""))

    return riders


def parse_speciality_points(html: str) -> dict[str, float]:
    """Parse the speciality-points panel from a PCS rider profile page."""
    soup = BeautifulSoup(html, "html.parser")
    points: dict[str, float] = {}
    # PCS renders these as "<speciality> <points>" pairs in a points list.
    for li in soup.select(".pps li, .speciality li, ul.basic li"):
        label = li.select_one(".title, .name")
        value = li.select_one(".pnt, .value, b")
        if not label or not value:
            continue
        key = label.get_text(strip=True).lower().replace(" ", "_").replace("-", "_")
        try:
            points[key] = float(re.sub(r"[^\d.]", "", value.get_text()) or 0)
        except ValueError:
            continue
    return points


# --- Adapters -------------------------------------------------------------

@dataclass
class StartlistAdapter:
    """Fetches the 2026 startlist from PCS and infers archetypes.

    `is_available()` gates the 'Preview - 2025' -> '2026 Live' transition: it's
    True once the race startlist page actually lists riders. Star prices are NOT
    on PCS — they default to 0 and are merged from the Tissot data when published.
    """

    season: int = 2026
    race_slug: str = "tour-de-france"
    client: PCSClient = field(default_factory=PCSClient)
    enrich_archetypes: bool = True

    @property
    def startlist_url(self) -> str:
        return f"{PCS_BASE}/race/{self.race_slug}/{self.season}/startlist"

    def _safe_fetch(self) -> list[ScrapedRider]:
        try:
            return parse_startlist(self.client.get(self.startlist_url))
        except (httpx.HTTPError, OSError):
            return []

    def is_available(self) -> bool:
        return len(self._safe_fetch()) > 0

    def fetch(self) -> list[ScrapedRider]:
        riders = self._safe_fetch()
        if self.enrich_archetypes:
            for r in riders:
                self._enrich(r)
        return riders

    def _enrich(self, rider: ScrapedRider) -> None:
        slug = rider.name.lower().replace(" ", "-")
        try:
            html = self.client.get(f"{PCS_BASE}/rider/{slug}")
            rider.archetype = infer_archetype(parse_speciality_points(html))
        except (httpx.HTTPError, OSError):
            pass  # keep default archetype; daily job retries


@dataclass
class FormAdapter:
    """Computes a 0..1 trailing-form score from a rider's recent PCS results."""

    client: PCSClient = field(default_factory=PCSClient)
    window: int = 10  # most-recent results to weigh

    def fetch_form(self, rider_names: list[str]) -> dict[str, float]:
        out: dict[str, float] = {}
        for name in rider_names:
            slug = name.lower().replace(" ", "-")
            try:
                html = self.client.get(f"{PCS_BASE}/rider/{slug}/results")
                out[name] = form_from_results(parse_recent_positions(html, self.window))
            except (httpx.HTTPError, OSError):
                continue
        return out


def parse_recent_positions(html: str, window: int) -> list[int]:
    """Extract the most-recent finishing positions from a PCS results table."""
    soup = BeautifulSoup(html, "html.parser")
    positions: list[int] = []
    for row in soup.select("table tbody tr"):
        cell = row.find("td")
        if not cell:
            continue
        txt = cell.get_text(strip=True)
        if txt.isdigit():
            positions.append(int(txt))
        if len(positions) >= window:
            break
    return positions


def form_from_results(positions: list[int]) -> float:
    """Map recent finishing positions to a 0..1 form score (better = higher)."""
    if not positions:
        return 0.5
    # Each result contributes more the nearer the win; average and clamp.
    scores = [max(0.0, 1.0 - (p - 1) / 50.0) for p in positions]
    return round(sum(scores) / len(scores), 3)
