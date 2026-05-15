"""Public AI Action request / result contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class AIActionRequest:
    """Business-level AI request.

    Callers pass domain payloads and refs, never raw provider prompts.
    """

    action: str
    profile: str
    payload: dict[str, Any]
    context_refs: list[str] = field(default_factory=list)
    preferred_backend: str | None = None
    require_review: bool = True


@dataclass(frozen=True)
class AIActionSpec:
    """Registered action contract and routing defaults."""

    name: str
    owner: str
    default_backend: str
    fallback_backend: str = "rule_fallback"
    output_mode: str = "json"
    activity_policy: str = "candidate"
    schema: dict[str, Any] | None = None
    prompt_id: str = ""
    prompt_version: str = "v1"
    temperature: float = 0.2


@dataclass
class AIActionResult:
    """Backend-independent AI action result."""

    ok: bool
    action: str
    backend: str
    run_id: str
    content: str = ""
    structured: dict[str, Any] | list[Any] | None = None
    warnings: list[str] = field(default_factory=list)
    error: str = ""
    activity_item_id: str = ""


class AIBackend(Protocol):
    """Backend protocol implemented by direct LLM, workflow, and agents."""

    name: str

    def run(
        self,
        request: AIActionRequest,
        spec: AIActionSpec,
    ) -> AIActionResult:
        """Run one AI action and return a normalized result."""


__all__ = [
    "AIActionRequest",
    "AIActionResult",
    "AIActionSpec",
    "AIBackend",
]
