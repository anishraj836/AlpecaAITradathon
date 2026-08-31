"""
Backwards-compatible Gemini client shim.
Delegates to the unified multi-provider LLM gateway in app.infrastructure.llm.
"""
from app.infrastructure.llm.client import llm_client as gemini_client, LLMClient as GeminiClient
from app.infrastructure.llm.providers.gemini import GeminiProvider

__all__ = ["gemini_client", "GeminiClient", "GeminiProvider"]
