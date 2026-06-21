"""Scraper adapter layer (PRD §8).

A thin adapter so a source change (PCS/FirstCycling/ASO) doesn't ripple into the
engine. v1 ships these as STUBS that return no rows; wire the real HTTP/parsing
in here without touching callers. Respect robots.txt, rate-limit politely, cache
aggressively — single-user personal use.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScrapedRider:
    name: str
    team: str
    archetype: str
    star_price: float
    form: float


class StartlistAdapter:
    """Watches for the 2026 Tissot startlist + star prices.

    Until ASO publishes (final ~week before the Grand Depart), `fetch` returns
    an empty list and the app stays in 'Preview - 2025 data' mode. On publish,
    implement the parse here; the ingest job flips the badge to '2026 Live' and
    recomputes every recommendation. It's a data swap, not a code change.
    """

    source = "pcs"  # procyclingstats.com

    def is_available(self) -> bool:
        """True once the real 2026 startlist/prices are published."""
        return False

    def fetch(self) -> list[ScrapedRider]:
        # TODO: httpx GET + BeautifulSoup parse of the PCS startlist + Tissot prices.
        return []


class FormAdapter:
    """Trailing-window results used to update Rider.form. Stubbed for v1."""

    def fetch_form(self, rider_names: list[str]) -> dict[str, float]:
        # TODO: scrape recent PCS results, normalise to a 0..1 form score.
        return {}
