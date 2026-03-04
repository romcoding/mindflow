"""
LLM Provider Abstraction Layer for MindFlow/Rovot.

Supports OpenAI, LM Studio, Ollama, and any OpenAI-compatible endpoint.
"""
from src.llm.provider import LlmProvider
from src.llm.factory import get_llm_provider

__all__ = ["LlmProvider", "get_llm_provider"]
