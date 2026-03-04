"""
OpenAI LLM provider implementation.

Works with the official OpenAI API as well as any OpenAI-compatible endpoint
(LM Studio, Ollama, vLLM, LocalAI, etc.) by setting a custom ``base_url``.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from src.llm.provider import ChatResponse, LlmProvider, ToolCall

logger = logging.getLogger(__name__)

# Default models per provider type
DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "lmstudio": "local-model",
    "ollama": "llama3",
    "custom": "default",
}


class OpenAIProvider(LlmProvider):
    """
    LLM provider backed by the ``openai`` Python SDK.

    Parameters
    ----------
    api_key : str, optional
        API key.  Falls back to ``OPENAI_API_KEY`` env var.
    base_url : str, optional
        Custom base URL.  Falls back to ``OPENAI_API_BASE`` env var.
        Set to ``http://localhost:1234/v1`` for LM Studio,
        ``http://localhost:11434/v1`` for Ollama, etc.
    default_model : str, optional
        Model name to use when none is specified per-call.
    provider_type : str
        One of ``"openai"``, ``"lmstudio"``, ``"ollama"``, ``"custom"``.
    """

    provider_name = "openai_compatible"

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        provider_type: str = "openai",
    ):
        self.provider_type = provider_type
        self._api_key = (api_key or os.environ.get("OPENAI_API_KEY", "")).strip()
        self._base_url = (base_url or os.environ.get("OPENAI_API_BASE", "")).strip() or None
        self._default_model = default_model or DEFAULT_MODELS.get(provider_type, "gpt-4o-mini")
        self._client = None

        # For local providers, a dummy key is acceptable
        if not self._api_key and provider_type in ("lmstudio", "ollama", "custom"):
            self._api_key = "lm-studio"  # dummy key for local servers

    # ------------------------------------------------------------------
    # Lazy client initialisation
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self._api_key:
            raise RuntimeError("No API key configured for the LLM provider.")
        try:
            from openai import OpenAI

            kwargs: Dict[str, Any] = {"api_key": self._api_key}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = OpenAI(**kwargs)
            logger.info(
                "OpenAI-compatible client initialised (type=%s, base_url=%s)",
                self.provider_type,
                self._base_url or "default",
            )
            return self._client
        except Exception as exc:
            logger.error("Failed to initialise OpenAI client: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Core implementation
    # ------------------------------------------------------------------

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
        client = self._get_client()
        model = model or self._default_model

        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
        if response_format:
            # Some local models don't support response_format; wrap in try
            kwargs["response_format"] = response_format

        try:
            raw = client.chat.completions.create(**kwargs)
        except Exception as exc:
            # If response_format caused the error, retry without it
            if response_format and "response_format" in str(exc):
                logger.warning("Provider does not support response_format, retrying without it.")
                kwargs.pop("response_format", None)
                raw = client.chat.completions.create(**kwargs)
            else:
                raise

        choice = raw.choices[0]
        msg = choice.message

        # Parse tool calls
        parsed_tool_calls: List[ToolCall] = []
        if msg.tool_calls:
            import json as _json

            for tc in msg.tool_calls:
                try:
                    args = _json.loads(tc.function.arguments)
                except (ValueError, TypeError):
                    args = {}
                parsed_tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        function_name=tc.function.name,
                        arguments=args,
                    )
                )

        usage = None
        if hasattr(raw, "usage") and raw.usage:
            usage = {
                "prompt_tokens": raw.usage.prompt_tokens,
                "completion_tokens": raw.usage.completion_tokens,
                "total_tokens": raw.usage.total_tokens,
            }

        return ChatResponse(
            content=msg.content,
            tool_calls=parsed_tool_calls,
            finish_reason=choice.finish_reason,
            usage=usage,
            raw=raw,
        )

    # ------------------------------------------------------------------
    # Availability check
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        try:
            self._get_client()
            return True
        except Exception:
            return False
