"""
Provider registry. Call get_llm() / get_voice() everywhere instead of
constructing adapters directly.
"""

from __future__ import annotations

from functools import lru_cache

from app.providers.base import (  # noqa: F401  (re-exported for callers)
    LLMProvider,
    LLMResponse,
    SynthResult,
    ToolCall,
    Transcript,
    VoiceProvider,
)


@lru_cache(maxsize=1)
def get_llm() -> LLMProvider:
    from app.providers.groq_llm import GroqLLM
    return GroqLLM()


@lru_cache(maxsize=1)
def get_voice() -> VoiceProvider:
    from app.providers.sahara_voice import SaharaVoice
    return SaharaVoice()
