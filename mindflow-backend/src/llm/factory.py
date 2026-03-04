"""
Factory for creating LLM provider instances.

The factory reads configuration from environment variables and/or
the database (per-user settings) and returns the appropriate provider.

Environment variables
---------------------
LLM_PROVIDER        : "openai" | "lmstudio" | "ollama" | "custom"  (default: "openai")
OPENAI_API_KEY       : API key for OpenAI (or dummy for local providers)
OPENAI_API_BASE      : Custom base URL (e.g. http://localhost:1234/v1)
LLM_MODEL            : Override the default model name
LLM_CUSTOM_BASE_URL  : Alternative to OPENAI_API_BASE for custom providers
LLM_CUSTOM_API_KEY   : Alternative to OPENAI_API_KEY for custom providers
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from src.llm.openai_provider import OpenAIProvider
from src.llm.provider import LlmProvider

logger = logging.getLogger(__name__)

# Module-level cache (one provider per configuration fingerprint)
_provider_cache: dict[str, LlmProvider] = {}

# Well-known local provider defaults
_LOCAL_DEFAULTS = {
    "lmstudio": {"base_url": "http://localhost:1234/v1", "model": "local-model"},
    "ollama": {"base_url": "http://localhost:11434/v1", "model": "llama3"},
}


def get_llm_provider(
    *,
    provider_type: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> LlmProvider:
    """
    Return a configured ``LlmProvider`` instance.

    Parameters are optional; when omitted the factory reads from
    environment variables.  Results are cached so that repeated calls
    with the same configuration reuse the same client.
    """
    ptype = (provider_type or os.environ.get("LLM_PROVIDER", "openai")).strip().lower()
    key = api_key or os.environ.get("LLM_CUSTOM_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    url = base_url or os.environ.get("LLM_CUSTOM_BASE_URL") or os.environ.get("OPENAI_API_BASE", "")
    mdl = model or os.environ.get("LLM_MODEL", "")

    # Apply well-known defaults for local providers
    if ptype in _LOCAL_DEFAULTS:
        if not url:
            url = _LOCAL_DEFAULTS[ptype]["base_url"]
        if not mdl:
            mdl = _LOCAL_DEFAULTS[ptype]["model"]

    cache_key = f"{ptype}|{key[:8] if key else ''}|{url}|{mdl}"
    if cache_key in _provider_cache:
        return _provider_cache[cache_key]

    logger.info(
        "Creating LLM provider: type=%s, base_url=%s, model=%s",
        ptype,
        url or "(default)",
        mdl or "(default)",
    )

    provider = OpenAIProvider(
        api_key=key or None,
        base_url=url or None,
        default_model=mdl or None,
        provider_type=ptype,
    )

    _provider_cache[cache_key] = provider
    return provider


def clear_provider_cache() -> None:
    """Clear the provider cache (useful when configuration changes)."""
    _provider_cache.clear()
    logger.info("LLM provider cache cleared.")
