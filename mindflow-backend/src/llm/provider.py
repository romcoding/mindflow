"""
Abstract base class for LLM providers.

All LLM providers (OpenAI, LM Studio, Ollama, etc.) implement this interface
so that the rest of the application is agnostic of the underlying service.
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A single message in a conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Any]] = None
    name: Optional[str] = None


@dataclass
class ToolCall:
    """Represents a tool/function call returned by the LLM."""
    id: str
    function_name: str
    arguments: Dict[str, Any]


@dataclass
class ChatResponse:
    """Standardised response from any LLM provider."""
    content: Optional[str] = None
    tool_calls: List[ToolCall] = field(default_factory=list)
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    raw: Any = None  # The raw response object from the SDK


class LlmProvider(ABC):
    """
    Abstract interface that every LLM backend must implement.

    Concrete subclasses only need to implement ``chat_completion``.
    Higher-level helpers (``classify_text``, ``extract_json``, etc.) are
    provided as convenience wrappers.
    """

    provider_name: str = "base"

    # ------------------------------------------------------------------
    # Core abstract method
    # ------------------------------------------------------------------

    @abstractmethod
    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        response_format: Optional[Dict] = None,
    ) -> ChatResponse:
        """Send a chat-completion request and return a ``ChatResponse``."""
        ...

    # ------------------------------------------------------------------
    # Convenience helpers (shared across all providers)
    # ------------------------------------------------------------------

    def classify_text(self, text: str, categories: List[str]) -> str:
        """Classify *text* into one of the given *categories*."""
        cats = ", ".join(f'"{c}"' for c in categories)
        messages = [
            {"role": "system", "content": f"Classify the following text into exactly one of these categories: {cats}. Respond with ONLY the category name, nothing else."},
            {"role": "user", "content": text},
        ]
        resp = self.chat_completion(messages, temperature=0.2, max_tokens=20)
        result = (resp.content or "").strip().strip('"').lower()
        # Ensure the result is one of the valid categories
        for cat in categories:
            if cat.lower() in result:
                return cat
        return categories[-1]  # fallback to last category

    def extract_json(self, text: str, system_prompt: str) -> Dict[str, Any]:
        """Ask the LLM to extract structured JSON from *text*."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]
        resp = self.chat_completion(
            messages,
            temperature=0.2,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(resp.content or "{}")
        except json.JSONDecodeError:
            logger.warning("LLM returned non-JSON content: %s", resp.content)
            return {}

    def summarise(self, text: str, *, max_words: int = 100) -> str:
        """Return a concise summary of *text*."""
        messages = [
            {"role": "system", "content": f"Summarise the following text in at most {max_words} words. Be concise and informative."},
            {"role": "user", "content": text},
        ]
        resp = self.chat_completion(messages, temperature=0.3, max_tokens=300)
        return resp.content or ""

    def is_available(self) -> bool:
        """Return ``True`` if the provider is configured and reachable."""
        try:
            resp = self.chat_completion(
                [{"role": "user", "content": "ping"}],
                temperature=0,
                max_tokens=5,
            )
            return resp.content is not None
        except Exception:
            return False
