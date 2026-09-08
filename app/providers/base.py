"""
Provider-agnostic interfaces for the reasoning brain and the voice layer.

Keeping these abstract means the consultation agent never imports Groq or Sahara
directly, and swapping either (Claude, Gemini, a different ASR) is one adapter.
"""

from __future__ import annotations

import abc
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

# ─────────────────────────────────────────────
# LLM
# ─────────────────────────────────────────────

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    model: str = ""
    usage: dict = field(default_factory=dict)

    @property
    def wants_tools(self) -> bool:
        return bool(self.tool_calls)


class LLMProvider(abc.ABC):
    """Chat completion with optional tool-calling. Messages are OpenAI-style
    dicts so the agent can accumulate history without an impedance mismatch."""

    name: str = "llm"

    @abc.abstractmethod
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
        reasoning_effort: str | None = None,
    ) -> LLMResponse:
        ...


# ─────────────────────────────────────────────
# VOICE
# ─────────────────────────────────────────────

@dataclass
class Transcript:
    text: str
    language: str | None = None
    duration_s: float | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class SynthResult:
    audio: bytes
    content_type: str = "audio/wav"
    duration_s: float | None = None


class VoiceProvider(abc.ABC):
    name: str = "voice"

    @abc.abstractmethod
    async def transcribe(
        self,
        audio: bytes,
        *,
        language: str = "en",
        filename: str = "audio.wav",
        telehealth: bool = True,
    ) -> Transcript:
        ...

    @abc.abstractmethod
    async def synthesize(self, text: str, *, language: str = "en") -> SynthResult:
        ...

    # Streaming — implemented in P1. Default raises so callers can feature-detect.
    def transcribe_stream(self, *args: Any, **kwargs: Any) -> AsyncIterator[dict]:
        raise NotImplementedError

    def synthesize_stream(self, *args: Any, **kwargs: Any) -> AsyncIterator[bytes]:
        raise NotImplementedError
