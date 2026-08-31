from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class BaseLLMProvider(ABC):
    """
    Abstract Base Class for Multi-Provider LLM Gateway in VOLTRON.
    Enforces unified asynchronous structured JSON reasoning across all LLM providers.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. "gemini", "openai", "groq", "anthropic", "ollama", "deepseek")."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the active model being invoked."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider has valid credentials and configuration."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        system_instruction: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.2,
    ) -> Optional[T]:
        """
        Generate structured output adhering strictly to the response_model Pydantic schema.
        Returns validated instance of response_model, or None on failure/fallback.
        """
        pass
