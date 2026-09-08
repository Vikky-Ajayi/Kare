"""
Process due proactive follow-ups once, then exit.

Railway cron:  every ~15 min  ->  python -m app.worker.followup_tick
Local dev:     the APScheduler job in app.main calls run_once() directly.
"""

from __future__ import annotations

import asyncio
import logging

from app.database import SessionLocal
from app.services import followups

log = logging.getLogger("kare.worker")


async def run_once() -> dict:
    db = SessionLocal()
    try:
        stats = await followups.process_due(db)
        if stats["considered"]:
            log.info("followup tick: %s", stats)
        return stats
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
    print(asyncio.run(run_once()))
