"""Shared LLM call runtime: structured output with light outer-retry wrapper.

instructor (used inside the real providers) already handles retry-with-validation
internally when `max_retries > 0`. We expose a thin wrapper to keep the call sites
uniform between Mock and Instructor providers, and to centralise overrides + error
context.
"""
from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel

from judgex.llm import LLMProvider, Message

T = TypeVar("T", bound=BaseModel)

DEFAULT_PROVIDER_RETRIES = 2


def call_model(
    provider: LLMProvider,
    system: str,
    user: str,
    response_model: type[T],
    overrides: dict[str, Any] | None = None,
    provider_retries: int = DEFAULT_PROVIDER_RETRIES,
) -> tuple[T, dict[str, Any]]:
    """Single structured-output call against `provider`, returning a validated instance.

    `overrides` are applied to the validated instance's dict before re-validation,
    so callers can force fields (persona_id, proposal_id, contributing_agents)
    to canonical values without trusting the model to set them correctly.

    `provider_retries` is forwarded to instructor's internal retry-on-validation
    loop. Mock provider ignores it.
    """
    messages = [Message(role="user", content=user)]
    instance = provider.complete_model(
        system=system,
        messages=messages,
        response_model=response_model,
        max_retries=provider_retries,
    )
    raw = instance.model_dump()
    if overrides:
        raw = {**raw, **overrides}
        instance = response_model.model_validate(raw)
    return instance, raw
