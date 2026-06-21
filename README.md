# Domestique — Tour de France Fantasy by Tissot Strategist

Personal decision-support app for the *Tour de France Fantasy by Tissot* game.
It projects per-rider fantasy points per stage, recommends the optimal opening
squad, the daily Stage-Winner-Bonus pick, and when to spend transfers.

See [docs/PRD.md](docs/PRD.md) for the full product spec.

> The app **recommends**; you execute moves on the Tissot site and keep the
> app's state in sync manually. Single-user, personal use.

## Repo layout

```
backend/    FastAPI service — ingest, projection engine, OR-Tools optimizer
frontend/   React PWA (Vite) — 5 screens, installable to phone home screen
docs/        Product requirements
```

## Quick start

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edit DATABASE_URL etc.
python -m app.ingest.seed     # load 2025 seed data (Preview mode)
uvicorn app.main:app --reload # http://localhost:8000  (docs at /docs)
```

### Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

## Status

This is a **scaffold**: runnable end-to-end against the 2025 seed dataset.
The rules-based projection engine and the OR-Tools initial-squad optimizer (P1)
are wired up; P2 (daily bonus) and P3 (transfer heuristic) have working
baselines; ML refinement (v1.1) and real 2026 data ingestion are stubbed
behind adapters.

## Data readiness

The app runs in **Preview — 2025 data** mode until the 2026 Tissot startlist and
star prices publish (typically the final week before the Grand Départ). A
scraper job watches for the real data; on publish it ingests, flips the badge to
**2026 Live**, and recomputes every recommendation. It's a data swap, not a code
change.
