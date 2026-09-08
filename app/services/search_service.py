"""
Search Service — DuckDuckGo (completely free, no API key).
Used by the AI doctor to look up drugs, treatments, guidelines
before drawing conclusions.

Install: pip install duckduckgo-search
"""

import asyncio


async def search_medical(query: str, max_results: int = 4) -> list[dict]:
    """Search DuckDuckGo for medical information."""
    try:
        from duckduckgo_search import DDGS

        def _sync_search():
            with DDGS() as ddgs:
                return list(ddgs.text(
                    query,
                    max_results=max_results,
                    safesearch="moderate",
                ))

        results = await asyncio.get_event_loop().run_in_executor(None, _sync_search)
        return [
            {
                "title": r.get("title", ""),
                "snippet": r.get("body", "")[:500],
                "url": r.get("href", ""),
            }
            for r in results if r.get("body")
        ]
    except ImportError:
        return []
    except Exception:
        return []


def format_for_prompt(results: list[dict]) -> str:
    if not results:
        return "No search results available."
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']}\n    {r['snippet']}")
    return "\n\n".join(lines)
