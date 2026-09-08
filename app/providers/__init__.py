"""
Provider registry. Call get_llm() / get_voice() everywhere instead of
constructing adapters directly.

Tests call use_test_providers(...) to swap in fakes; because the override check
lives inside get_llm/get_voice, it works even for modules that did
`from app.providers import get_llm`.
"""

from __future__ import annotations

from app.providers.base import (  # noqa: F401  (re-exported for callers)
    LLMProvider,
    LLMResponse,
    SynthResult,
    ToolCall,
    Transcript,
    VoiceProvider,
)

_llm: LLMProvider | None = None
_voice: VoiceProvider | None = None
_llm_override: LLMProvider | None = None
_voice_override: VoiceProvider | None = None


def get_llm() -> LLMProvider:
    if _llm_override is not None:
        return _llm_override
    global _llm
    if _llm is None:
        from app.providers.groq_llm import GroqLLM
        _llm = GroqLLM()
    return _llm


def get_voice() -> VoiceProvider:
    if _voice_override is not None:
        return _voice_override
    global _voice
    if _voice is None:
        from app.providers.sahara_voice import SaharaVoice
        _voice = SaharaVoice()
    return _voice


def use_test_providers(llm: LLMProvider | None = None, voice: VoiceProvider | None = None) -> None:
    global _llm_override, _voice_override
    _llm_override = llm
    _voice_override = voice
