"""
The consultation agent loop: model -> tool calls -> execute -> model -> ... until
the model produces a spoken reply or the iteration cap is hit.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from app.agent.tools import EXECUTORS, TOOL_SCHEMAS, ToolContext
from app.providers import get_llm

log = logging.getLogger("kare.agent")

MAX_ITERS = 3  # tools on iters 0-1, forced plain answer on iter 2
_FALLBACK = "I'm sorry, I didn't catch that — could you say it again?"


@dataclass
class AgentResult:
    reply: str
    tool_calls: list[str] = field(default_factory=list)
    usage_tokens: int = 0


async def run_agent(
    ctx: ToolContext,
    *,
    system_prompt: str,
    history: list[dict],
    user_message: str,
    tools: list[dict] | None = None,
) -> AgentResult:
    llm = get_llm()
    tool_schemas = tools if tools is not None else TOOL_SCHEMAS

    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    messages += history
    messages.append({"role": "user", "content": user_message})

    made: list[str] = []
    total_tokens = 0

    for i in range(MAX_ITERS):
        force_answer = i == MAX_ITERS - 1
        resp = await llm.complete(
            messages,
            tools=None if force_answer else tool_schemas,
            tool_choice="auto",
            temperature=0.4,
            max_tokens=500,
            reasoning_effort="low",
        )
        total_tokens += resp.usage.get("total_tokens", 0)

        if not resp.tool_calls:
            return AgentResult(
                reply=resp.content.strip() or _FALLBACK,
                tool_calls=made,
                usage_tokens=total_tokens,
            )

        # record the assistant's tool-call message
        messages.append({
            "role": "assistant",
            "content": resp.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)}}
                for tc in resp.tool_calls
            ],
        })

        for tc in resp.tool_calls:
            made.append(tc.name)
            executor = EXECUTORS.get(tc.name)
            if executor is None:
                result = {"error": f"unknown tool {tc.name}"}
            else:
                try:
                    result = await executor(ctx, **tc.arguments)
                except TypeError as exc:
                    result = {"error": f"bad arguments: {exc}"}
                except Exception as exc:  # noqa: BLE001
                    log.warning("tool %s failed: %s", tc.name, exc)
                    result = {"error": str(exc)}
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, default=str)[:4000],
            })

    # exhausted iterations without a plain answer — ask once more, no tools
    resp = await llm.complete(messages, temperature=0.4, max_tokens=500, reasoning_effort="low")
    return AgentResult(
        reply=resp.content.strip() or _FALLBACK,
        tool_calls=made,
        usage_tokens=total_tokens + resp.usage.get("total_tokens", 0),
    )
