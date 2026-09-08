"""
Web search for the consultation agent (drug info, treatment guidelines).
Uses ddgs (formerly duckduckgo-search) — free, no key. Best-effort: on any
failure it returns nothing and the agent proceeds without it.
"""

from __future__ import annotations

import asyncio
import logging

log = logging.getLogger("kare.search")


async def search_medical(query: str, max_results: int = 4) -> list[dict]:
    def _sync() -> list[dict]:
        try:
            from ddgs import DDGS
        except ImportError:  # pragma: no cover
            return []
        try:
            with DDGS() as ddgs:
                rows = list(ddgs.text(query, max_results=max_results, safesearch="moderate"))
        except Exception as exc:  # noqa: BLE001
            log.info("web search failed: %s", exc)
            return []
        return [
            {"title": r.get("title", ""), "snippet": (r.get("body") or "")[:500], "url": r.get("href", "")}
            for r in rows
            if r.get("body")
        ]

    return await asyncio.get_running_loop().run_in_executor(None, _sync)


def format_for_prompt(results: list[dict]) -> str:
    if not results:
        return "No search results available."
    return "\n\n".join(f"[{i}] {r['title']}\n    {r['snippet']}" for i, r in enumerate(results, 1))
