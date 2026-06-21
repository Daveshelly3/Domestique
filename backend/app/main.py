"""Domestique FastAPI app entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routers import push, riders, squad, stages, team, transfers


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Domestique", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(squad.router)
app.include_router(stages.router)
app.include_router(transfers.router)
app.include_router(team.router)
app.include_router(riders.router)
app.include_router(push.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "app": "domestique"}
