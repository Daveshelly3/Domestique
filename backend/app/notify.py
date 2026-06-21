"""Web-push deadline notifications (PRD §10).

Delivered via VAPID web push from the PWA service worker. iOS caveat: only fires
if the PWA is added to the home screen on iOS 16.4+. Generate VAPID keys with:

    python -m app.notify generate-keys
"""
from __future__ import annotations

import json
import sys

from .config import settings


def generate_keys() -> None:
    """Print a fresh VAPID keypair for .env."""
    from py_vapid import Vapid  # provided by pywebpush

    v = Vapid()
    v.generate_keys()
    print("VAPID_PUBLIC_KEY=", v.public_key)  # noqa: T201
    print("VAPID_PRIVATE_KEY=", v.private_key)  # noqa: T201


def send_push(subscription: dict, title: str, body: str) -> None:
    """Send a single web-push message. No-op if VAPID keys are unset."""
    if not settings.vapid_private_key:
        return
    from pywebpush import webpush

    webpush(
        subscription_info=subscription,
        data=json.dumps({"title": title, "body": body}),
        vapid_private_key=settings.vapid_private_key,
        vapid_claims={"sub": settings.vapid_subject},
    )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "generate-keys":
        generate_keys()
    else:
        print("usage: python -m app.notify generate-keys")  # noqa: T201
