from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any


CHARS_PER_TOKEN = 3.2


class LocalLLMBudgetError(RuntimeError):
    error_type = "llm_context_budget_exceeded"


@dataclass(frozen=True)
class LocalLLMBudget:
    context_window: int = 8192
    max_output_tokens: int = 1024
    max_input_tokens: int = 6000
    max_input_chars: int = 22000
    safety_margin_tokens: int = 512
    truncation_strategy: str = "preserve_head"

    @classmethod
    def from_settings(cls, settings: Any) -> "LocalLLMBudget":
        return cls(
            context_window=_setting(settings, "local_llm_context_window", 8192),
            max_output_tokens=_setting(
                settings,
                "local_llm_max_output_tokens",
                _setting(settings, "local_llm_max_tokens", _setting(settings, "local_llm_max_new_tokens", 1024)),
            ),
            max_input_tokens=_setting(settings, "local_llm_max_input_tokens", 6000),
            max_input_chars=_setting(settings, "local_llm_max_input_chars", 22000),
            safety_margin_tokens=_setting(settings, "local_llm_safety_margin_tokens", 512),
            truncation_strategy=str(
                getattr(settings, "local_llm_truncation_strategy", "preserve_head")
            ),
        )

    @property
    def effective_input_tokens(self) -> int:
        return min(
            self.max_input_tokens,
            self.context_window - self.max_output_tokens - self.safety_margin_tokens,
        )

    def prepare(self, *, system_prompt: str, user_content: str, chunked: bool = False) -> tuple[str, dict[str, Any]]:
        if self.context_window <= 0 or self.max_output_tokens <= 0:
            raise LocalLLMBudgetError("LLM context_window and max_output_tokens must be positive.")
        available_tokens = self.effective_input_tokens
        system_tokens = estimate_tokens(system_prompt)
        if available_tokens <= system_tokens:
            raise LocalLLMBudgetError(
                "System prompt exceeds the configured Local LLM input budget."
            )

        max_user_tokens = available_tokens - system_tokens
        available_chars = self.max_input_chars - len(system_prompt)
        if available_chars <= 0:
            raise LocalLLMBudgetError(
                "System prompt exceeds LOCAL_LLM_MAX_INPUT_CHARS."
            )
        max_user_chars = min(available_chars, int(max_user_tokens * CHARS_PER_TOKEN))
        original = user_content
        truncated = len(original) > max_user_chars or estimate_tokens(original) > max_user_tokens
        if truncated:
            if self.truncation_strategy != "preserve_head":
                raise LocalLLMBudgetError(
                    f"Unsupported LOCAL_LLM_TRUNCATION_STRATEGY={self.truncation_strategy!r}."
                )
            user_content = original[:max_user_chars]
            while user_content and estimate_tokens(user_content) > max_user_tokens:
                user_content = user_content[:-1]

        total_chars = len(system_prompt) + len(user_content)
        total_tokens = estimate_tokens(system_prompt) + estimate_tokens(user_content)
        budget_ok = (
            total_tokens + self.max_output_tokens + self.safety_margin_tokens
            <= self.context_window
        )
        metadata = {
            "input_chars": total_chars,
            "estimated_input_tokens": total_tokens,
            "max_output_tokens": self.max_output_tokens,
            "context_window": self.context_window,
            "safety_margin_tokens": self.safety_margin_tokens,
            "budget_ok": budget_ok,
            "truncated": truncated,
            "chunked": chunked,
        }
        if not budget_ok:
            raise LocalLLMBudgetError(
                "Local LLM request still exceeds the configured context budget after truncation."
            )
        return user_content, metadata

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / CHARS_PER_TOKEN) if text else 0


def _setting(settings: Any, name: str, default: int) -> int:
    try:
        return int(getattr(settings, name, default))
    except (TypeError, ValueError):
        return default
