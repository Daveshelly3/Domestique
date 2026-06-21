"""Application settings and game constants."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

DATA_DIR = Path(__file__).parent / "data"


class Settings(BaseSettings):
    """Environment-driven settings.

    Falls back to a local SQLite file when DATABASE_URL is unset so the app
    runs end-to-end without a Postgres instance.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = f"sqlite:///{Path(__file__).parent.parent / 'domestique.sqlite3'}"
    frontend_origin: str = "http://localhost:5173"

    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:you@example.com"


settings = Settings()


# --- Game constants (official 2026 rules; see PRD §3) ---------------------
BUDGET_STARS = 120
SQUAD_SIZE = 8
CATEGORY_CAPS = {
    "leader": 3,
    "all_rounder": 5,
    "sprinter": 3,
    "climber": 3,
}
TOTAL_TRANSFERS = 8
BREAKAWAY_POINTS_PER_KM = 1
NUM_STAGES = 21

# Archetypes used throughout the engine. Must match CATEGORY_CAPS keys.
ARCHETYPES = tuple(CATEGORY_CAPS.keys())
