"""Pluggable LLM client.

All real providers go through `instructor` so that structured output works the same
way regardless of backend (Anthropic, OpenAI-compatible endpoint like a self-hosted
vLLM/Ollama/TGI cluster, etc.). The architecture nodes only ever pass a Pydantic
model class; the provider returns a validated instance.

Providers:
  - MockProvider: deterministic schema-conformant fake completions for pipeline tests
                  without API access.
  - AnthropicInstructorProvider: Claude via Anthropic SDK + instructor.
  - OpenAICompatibleInstructorProvider: any OpenAI-compatible endpoint (OpenAI proper,
                  vLLM, Ollama, TGI, llama.cpp server, custom university cluster).

Switching the production provider only requires changing JUDGEX_PROVIDER (and
JUDGEX_BASE_URL for self-hosted clusters) in .env. Architectures, schemas, runtime,
and personas stay untouched.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


# ---------------------------------------------------------------------------
# Provider protocol
# ---------------------------------------------------------------------------


@dataclass
class Message:
    role: str  # "user" | "assistant"
    content: str


class LLMProvider(Protocol):
    name: str
    model: str

    def complete_model(
        self,
        system: str,
        messages: list[Message],
        response_model: type[T],
        max_retries: int = 0,
    ) -> T:
        """Return a validated instance of `response_model`.

        `max_retries` here refers to the provider's *internal* validation retries
        (instructor's `max_retries`). Our `runtime.py` layer adds an outer retry
        loop with explicit feedback that runs on top of this.
        """
        ...


# ---------------------------------------------------------------------------
# Mock provider
# ---------------------------------------------------------------------------


def _seed_from(*parts: str) -> int:
    h = hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def _resolve_ref(schema: dict[str, Any], root: dict[str, Any]) -> dict[str, Any]:
    ref = schema.get("$ref")
    if not ref:
        return schema
    if not ref.startswith("#/$defs/"):
        raise ValueError(f"Unsupported $ref form: {ref}")
    name = ref.split("/")[-1]
    return root.get("$defs", {}).get(name, {})


def _pick_type(schema: dict[str, Any]) -> str | None:
    if "type" in schema:
        return schema["type"]
    for key in ("anyOf", "oneOf"):
        if key in schema:
            for branch in schema[key]:
                if branch.get("type") not in (None, "null"):
                    return branch.get("type")
    return None


def _mock_value(prop_schema: dict[str, Any], seed: int, path: str, root: dict[str, Any]) -> Any:
    prop_schema = _resolve_ref(prop_schema, root)
    if "type" not in prop_schema and "properties" not in prop_schema:
        for key in ("anyOf", "oneOf"):
            if key in prop_schema:
                for branch in prop_schema[key]:
                    resolved = _resolve_ref(branch, root)
                    if resolved.get("type") != "null":
                        return _mock_value(resolved, seed, path, root)
    t = _pick_type(prop_schema)
    if "enum" in prop_schema:
        choices = prop_schema["enum"]
        return choices[seed % len(choices)]
    if t == "integer":
        lo = prop_schema.get("minimum", 1)
        hi = prop_schema.get("maximum", 5)
        return lo + (seed % (hi - lo + 1))
    if t == "number":
        lo = prop_schema.get("minimum", 0.0)
        hi = prop_schema.get("maximum", 1.0)
        return round(lo + ((seed % 1000) / 1000.0) * (hi - lo), 3)
    if t == "string":
        return f"[mock:{path}]"
    if t == "array":
        item_schema = prop_schema.get("items", {"type": "string"})
        n = 1 + (seed % 2)
        return [_mock_value(item_schema, seed + i, f"{path}[{i}]", root) for i in range(n)]
    if t == "object" or "properties" in prop_schema:
        out: dict[str, Any] = {}
        props = prop_schema.get("properties", {})
        required = set(prop_schema.get("required", list(props.keys())))
        for k, sub in props.items():
            if k in required:
                out[k] = _mock_value(sub, _seed_from(path, k, str(seed)), f"{path}.{k}", root)
        return out
    return None


class MockProvider:
    name = "mock"
    model = "mock"

    def complete_model(
        self,
        system: str,
        messages: list[Message],
        response_model: type[T],
        max_retries: int = 0,
    ) -> T:
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        schema = response_model.model_json_schema()
        seed = _seed_from(system, last_user, response_model.__name__)
        raw = _mock_value(schema, seed, response_model.__name__, schema)
        return response_model.model_validate(raw)


# ---------------------------------------------------------------------------
# Real providers (via instructor)
# ---------------------------------------------------------------------------


DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 4096


class AnthropicInstructorProvider:
    """Claude via Anthropic SDK, wrapped in instructor for structured output."""

    name = "anthropic"

    def __init__(self, model: str | None = None, max_tokens: int = DEFAULT_MAX_TOKENS):
        from anthropic import Anthropic
        import instructor

        self.model = model or os.environ.get("JUDGEX_MODEL", "claude-sonnet-4-6")
        self.max_tokens = max_tokens
        self.client = instructor.from_anthropic(Anthropic())

    def complete_model(
        self,
        system: str,
        messages: list[Message],
        response_model: type[T],
        max_retries: int = 0,
    ) -> T:
        return self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=DEFAULT_TEMPERATURE,
            system=system,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            response_model=response_model,
            max_retries=max_retries,
        )


class OpenAICompatibleInstructorProvider:
    """OpenAI-compatible endpoint via instructor.

    Use cases:
      - OpenAI proper (omit base_url, set api_key)
      - Self-hosted vLLM / Ollama / TGI / llama.cpp server (set base_url)
      - University cluster exposing OpenAI-compatible API

    Configured via env vars:
      JUDGEX_MODEL      - model name as understood by the endpoint
      JUDGEX_BASE_URL   - optional, e.g. https://cluster.uni.local/v1
      JUDGEX_API_KEY    - optional, falls back to OPENAI_API_KEY, then to a dummy
                          string (some self-hosted servers don't enforce auth)
    """

    name = "openai_compatible"

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        disable_thinking: bool | None = None,
    ):
        from openai import OpenAI
        import instructor

        self.model = model or os.environ.get("JUDGEX_MODEL", "gpt-4o-mini")
        self.max_tokens = max_tokens
        resolved_base_url = base_url or os.environ.get("JUDGEX_BASE_URL") or None
        resolved_api_key = (
            api_key
            or os.environ.get("JUDGEX_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or "not-required"
        )
        # Read from env if not explicitly passed; default True for self-hosted vLLM endpoints
        # that serve Qwen3/DeepSeek-R1 thinking models (Blablador alias-large/-huge).
        if disable_thinking is None:
            env_val = os.environ.get("JUDGEX_DISABLE_THINKING", "true").lower()
            disable_thinking = env_val not in ("0", "false", "no")
        self.disable_thinking = disable_thinking
        client = OpenAI(api_key=resolved_api_key, base_url=resolved_base_url)
        # Mode.JSON is used instead of Mode.TOOLS because self-hosted endpoints
        # (vLLM, Blablador) often drop the connection when receiving tool-call requests.
        self.client = instructor.from_openai(client, mode=instructor.Mode.JSON)

    def complete_model(
        self,
        system: str,
        messages: list[Message],
        response_model: type[T],
        max_retries: int = 0,
    ) -> T:
        import time
        from openai import APIConnectionError

        composed = [{"role": "system", "content": system}] + [
            {"role": m.role, "content": m.content} for m in messages
        ]
        extra: dict = {}
        if self.disable_thinking:
            # Disables Qwen3/DeepSeek-R1 extended-thinking via vLLM chat template flag.
            extra["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}

        # Outer retry for transient server errors (502 Bad Gateway, stale connections).
        from openai import InternalServerError

        for conn_attempt in range(4):
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    temperature=DEFAULT_TEMPERATURE,
                    max_tokens=self.max_tokens,
                    messages=composed,
                    response_model=response_model,
                    max_retries=max_retries,
                    **extra,
                )
            except (APIConnectionError, InternalServerError) as exc:
                if conn_attempt == 3:
                    raise
                wait = 30 * (conn_attempt + 1)
                print(f"[llm] transient error ({type(exc).__name__}), retrying in {wait}s (attempt {conn_attempt + 1}/3)…", flush=True)
                time.sleep(wait)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_provider(name: str | None = None) -> LLMProvider:
    """Resolve a provider by name. `name` defaults to JUDGEX_PROVIDER env var, then 'mock'."""
    resolved = (name or os.environ.get("JUDGEX_PROVIDER") or "mock").lower()
    if resolved == "mock":
        return MockProvider()
    if resolved == "anthropic":
        return AnthropicInstructorProvider()
    if resolved == "openai_compatible":
        return OpenAICompatibleInstructorProvider()
    raise ValueError(
        f"Unknown provider: {resolved}. Known: mock, anthropic, openai_compatible."
    )
