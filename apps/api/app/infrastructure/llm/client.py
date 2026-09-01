import logging
from typing import Optional, Type, TypeVar
from pydantic import BaseModel
from app.infrastructure.llm.base import BaseLLMProvider
from app.infrastructure.llm.factory import LLMFactory

logger = logging.getLogger("VoltronLLMClient")
T = TypeVar("T", bound=BaseModel)

class LLMClient:
    """
    Unified Multi-Provider LLM Gateway for VOLTRON.
    Delegates structured reasoning dynamically to the configured provider (Gemini, OpenAI, Groq, Anthropic, Ollama, DeepSeek).
    """

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self._provider = provider or LLMFactory.create_provider()

    @property
    def provider(self) -> BaseLLMProvider:
        return self._provider

    @property
    def provider_name(self) -> str:
        return self._provider.provider_name

    @property
    def model_name(self) -> str:
        return self._provider.model_name

    @property
    def is_configured(self) -> bool:
        return self._provider.is_configured

    def reload_provider(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Switch or reconfigure the LLM provider at runtime."""
        self._provider = LLMFactory.create_provider(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
        )
        logger.info(f"Reloaded LLM Provider: {self._provider.provider_name} ({self._provider.model_name})")

    async def generate_structured(
        self,
        system_instruction: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.2,
        cache_key: Optional[str] = None,
    ) -> Optional[T]:
        """
        Generate structured output adhering to the Pydantic response_model.
        Respects RateLimitGuard to prevent 429 quota exhaustion.
        """
        from app.infrastructure.llm.rate_limiter import quota_guard

        if cache_key:
            cached = quota_guard.get_cached(cache_key)
            if cached and isinstance(cached, response_model):
                return cached

        # Paces request through sliding window limiter
        await quota_guard.acquire_slot()

        res = await self._provider.generate_structured(
            system_instruction=system_instruction,
            user_prompt=user_prompt,
            response_model=response_model,
            temperature=temperature,
        )
        if res and cache_key:
            quota_guard.set_cached(cache_key, res)
        return res

# Global singleton client instance
llm_client = LLMClient()
