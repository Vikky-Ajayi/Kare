"""
Groq implementation of LLMProvider.

Default model is openai/gpt-oss-120b for consultation and follow-up writing;
callers pass model=settings.GROQ_LLM_MODEL_FAST for cheap background jobs
(note extraction, classification, translation).

gpt-oss models spend a large share of the output budget on hidden reasoning
tokens, so max_tokens is set generously and reasoning_effort defaults to "low"
for conversational turns.
"""

from __future__ import annotations

import json
import logging

from groq import AsyncGroq
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.providers.base import LLMProvider, LLMResponse, ToolCall

log = logging.getLogger("kare.llm")

_client: AsyncGroq | None = None


def _groq() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.GROQ_API_KEY, max_retries=0)
    return _client


class _Retryable(Exception):
    pass


class GroqLLM(LLMProvider):
    name = "groq"

    @retry(
        retry=retry_if_exception_type(_Retryable),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=1, max=20),
        reraise=True,
    )
    async def complete(
        self,
        messages: list[dict],
        *,
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
        temperature: float = 0.4,
        max_tokens: int = 1024,
        model: str | None = None,
        json_mode: bool = False,
        reasoning_effort: str | None = "low",
    ) -> LLMResponse:
        kwargs: dict = {
            "model": model or settings.GROQ_LLM_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if reasoning_effort and "gpt-oss" in kwargs["model"]:
            kwargs["reasoning_effort"] = reasoning_effort

        try:
            resp = await _groq().chat.completions.create(**kwargs)
        except Exception as exc:  # noqa: BLE001
            status = getattr(exc, "status_code", None)
            if status in (408, 409, 429, 500, 502, 503, 504):
                log.warning("Groq transient error %s, retrying: %s", status, exc)
                raise _Retryable(str(exc)) from exc
            raise

        choice = resp.choices[0]
        msg = choice.message
        calls: list[ToolCall] = []
        for tc in (msg.tool_calls or []):
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {"_raw": tc.function.arguments}
            calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))

        usage = {}
        if resp.usage:
            usage = {
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
                "total_tokens": resp.usage.total_tokens,
            }

        return LLMResponse(
            content=msg.content or "",
            tool_calls=calls,
            finish_reason=choice.finish_reason or "stop",
            model=resp.model,
            usage=usage,
        )
