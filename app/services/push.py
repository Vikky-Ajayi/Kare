"""
Web Push delivery (VAPID + pywebpush). Best-effort: a dead endpoint is
deactivated, everything else is logged and swallowed so a push failure never
breaks a follow-up.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.models import PushSubscription

log = logging.getLogger("kare.push")


def _vapid_claims() -> dict:
    return {"sub": settings.VAPID_SUBJECT}


def send_to_user(db: Session, user_id: str, *, title: str, body: str, url: str,
                 tag: str = "kare-followup") -> int:
    """Push to every active subscription for the user. Returns how many succeeded."""
    if not settings.VAPID_PRIVATE_KEY:
        log.warning("VAPID_PRIVATE_KEY not set — skipping push")
        return 0

    from pywebpush import WebPushException, webpush

    subs = (
        db.query(PushSubscription)
        .filter(PushSubscription.user_id == user_id, PushSubscription.is_active.is_(True))
        .all()
    )
    payload = json.dumps({"title": title, "body": body, "url": url, "tag": tag})
    ok = 0
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims=dict(_vapid_claims()),
                ttl=60 * 60 * 12,
            )
            ok += 1
        except WebPushException as exc:
            code = getattr(exc.response, "status_code", None)
            if code in (404, 410):   # gone — deactivate
                sub.is_active = False
                log.info("push endpoint gone, deactivated (sub=%s)", sub.id)
            else:
                log.warning("push failed (sub=%s, %s): %s", sub.id, code, exc)
        except Exception as exc:  # noqa: BLE001
            log.warning("push error (sub=%s): %s", sub.id, exc)
    db.commit()
    return ok
