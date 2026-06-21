"""Web-push subscription endpoints (PRD §10)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import PushSubscription
from ..schemas import PushSubscriptionIn

router = APIRouter(prefix="/push", tags=["push"])


@router.get("/vapid-public-key")
def vapid_public_key():
    return {"key": settings.vapid_public_key}


@router.post("/subscribe")
def subscribe(sub: PushSubscriptionIn, db: Session = Depends(get_db)):
    existing = db.query(PushSubscription).filter_by(endpoint=sub.endpoint).first()
    if not existing:
        db.add(
            PushSubscription(
                endpoint=sub.endpoint,
                p256dh=sub.keys.get("p256dh", ""),
                auth=sub.keys.get("auth", ""),
            )
        )
        db.commit()
    return {"subscribed": True}
