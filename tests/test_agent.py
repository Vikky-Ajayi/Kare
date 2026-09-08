"""Fast unit tests for the red-flag keyword filter and the agent loop
(no network — the loop test drives a scripted fake LLM)."""

from __future__ import annotations

import json

import pytest

from app.agent import redflags
from app.agent.loop import run_agent
from app.agent.tools import ToolContext
from app.providers.base import LLMResponse, ToolCall


@pytest.mark.parametrize("text,pregnant,expected", [
    ("My chest dey pain me and e hard for me to breathe", False, True),
    ("I no fit breathe well since morning", False, True),
    ("I don dey vomit blood", False, True),
    ("one side of my body just weak", False, True),
    ("I wan kill myself", False, True),
    ("bitten by a snake for farm", False, True),
    ("small headache and body dey hot", False, False),
    ("my knee dey pain when I climb stairs", False, False),
    ("the baby never move since yesterday", True, True),
    ("my water just burst", True, True),
    ("I see small blood for my pad", True, True),
    ("baby dey kick well well today", True, False),
])
def test_keyword_redflags(text, pregnant, expected):
    got = redflags.keyword_check(text, pregnant=pregnant)
    assert bool(got) is expected


def test_keyword_pregnancy_flags_only_when_pregnant():
    assert redflags.keyword_check("the baby is not moving", pregnant=False) is None
    assert redflags.keyword_check("the baby is not moving", pregnant=True) is not None


class _ScriptedLLM:
    """Calls one tool, then answers with what it learned."""
    def __init__(self):
        self.turn = 0

    async def complete(self, messages, *, tools=None, **kw):
        self.turn += 1
        if self.turn == 1:
            return LLMResponse(
                content="", finish_reason="tool_calls", model="fake",
                tool_calls=[ToolCall(id="t1", name="score_triage",
                                     arguments={"level": "urgent", "reasoning": "worsening"})],
            )
        last_tool = next((m for m in reversed(messages) if m["role"] == "tool"), None)
        assert last_tool and json.loads(last_tool["content"])["recorded"] == "urgent"
        return LLMResponse(content="Based on what you've told me, please see a clinic today.",
                           finish_reason="stop", model="fake")


@pytest.mark.asyncio
async def test_agent_loop_executes_tool_then_answers(db):
    from app.models import Conversation, Patient, User
    from app.providers import use_test_providers

    user = User(email="a@b.c", hashed_password="x", is_active=True)
    db.add(user)
    db.flush()
    db.add(Patient(user_id=user.id, first_name="A", last_name="B"))
    db.flush()
    conv = Conversation(user_id=user.id, language="en")
    db.add(conv)
    db.flush()

    use_test_providers(llm=_ScriptedLLM())
    try:
        ctx = ToolContext(db=db, user=user, conversation=conv, language="en")
        result = await run_agent(ctx, system_prompt="sys", history=[], user_message="I feel worse")
        assert "score_triage" in result.tool_calls
        assert "clinic" in result.reply
        assert conv.triage_result == "urgent"
    finally:
        use_test_providers(None, None)
