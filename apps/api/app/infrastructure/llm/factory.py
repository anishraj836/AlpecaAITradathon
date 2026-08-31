import logging
from typing import Optional
from app.config import settings
from app.infrastructure.llm.base import BaseLLMProvider
from app.infrastructure.llm.providers.gemini import GeminiProvider
from app.infrastructure.llm.providers.openai_compatible import OpenAICompatibleProvider
from app.infrastructure.llm.providers.anthropic import AnthropicProvider
from app.infrastructure.llm.providers.ollama import OllamaProvider

logger = logging.getLogger("VoltronLLMFactory")

class LLMFactory:
    """
    Factory for instantiating the active LLM Provider in VOLTRON.
    Enables zero-friction pluggability across Gemini, OpenAI, Groq, Anthropic, DeepSeek, Ollama, etc.
    """

    @staticmethod
    def create_provider(
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> BaseLLMProvider:
        prov = (provider or getattr(settings, "LLM_PROVIDER", "gemini")).lower()

        # 1. Google Gemini
        if prov in ["gemini", "google"]:
            key = api_key or getattr(settings, "GEMINI_API_KEY", None) or getattr(settings, "LLM_API_KEY", None)
            m = model or getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite")
            logger.info(f"Initialized LLM Provider: Google Gemini ({m})")
            return GeminiProvider(api_key=key, model=m)

        # 2. OpenAI
        elif prov in ["openai", "chatgpt"]:
            key = api_key or getattr(settings, "OPENAI_API_KEY", None) or getattr(settings, "LLM_API_KEY", None)
            m = model or getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
            url = base_url or getattr(settings, "OPENAI_BASE_URL", "https://api.openai.com/v1")
            logger.info(f"Initialized LLM Provider: OpenAI ({m})")
            return OpenAICompatibleProvider(api_key=key, model=m, base_url=url, provider_name="openai")

        # 3. Groq Cloud (Ultra Fast LPUs)
        elif prov in ["groq"]:
            key = api_key or getattr(settings, "GROQ_API_KEY", None) or getattr(settings, "LLM_API_KEY", None)
            m = model or getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")
            url = base_url or "https://api.groq.com/openai/v1"
            logger.info(f"Initialized LLM Provider: Groq ({m})")
            return OpenAICompatibleProvider(api_key=key, model=m, base_url=url, provider_name="groq")

        # 4. Anthropic Claude
        elif prov in ["anthropic", "claude"]:
            key = api_key or getattr(settings, "ANTHROPIC_API_KEY", None) or getattr(settings, "LLM_API_KEY", None)
            m = model or getattr(settings, "ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
            logger.info(f"Initialized LLM Provider: Anthropic Claude ({m})")
            return AnthropicProvider(api_key=key, model=m)

        # 5. DeepSeek
        elif prov in ["deepseek"]:
            key = api_key or getattr(settings, "DEEPSEEK_API_KEY", None) or getattr(settings, "LLM_API_KEY", None)
            m = model or getattr(settings, "DEEPSEEK_MODEL", "deepseek-chat")
            url = base_url or "https://api.deepseek.com/v1"
            logger.info(f"Initialized LLM Provider: DeepSeek ({m})")
            return OpenAICompatibleProvider(api_key=key, model=m, base_url=url, provider_name="deepseek")

        # 6. Local Ollama (100% Offline)
        elif prov in ["ollama", "local"]:
            url = base_url or getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
            m = model or getattr(settings, "OLLAMA_MODEL", "llama3.2:3b")
            logger.info(f"Initialized LLM Provider: Local Ollama ({m}) at {url}")
            return OllamaProvider(base_url=url, model=m)

        # 7. Generic OpenAI-Compatible / Custom Endpoint
        elif prov in ["custom", "openrouter", "together"]:
            key = api_key or getattr(settings, "LLM_API_KEY", None)
            m = model or getattr(settings, "LLM_MODEL", "default")
            url = base_url or getattr(settings, "LLM_BASE_URL", "http://localhost:8000/v1")
            logger.info(f"Initialized Custom OpenAI-Compatible Provider: {prov} ({m}) at {url}")
            return OpenAICompatibleProvider(api_key=key, model=m, base_url=url, provider_name=prov)

        # Default fallback to Gemini
        else:
            key = api_key or getattr(settings, "GEMINI_API_KEY", None) or getattr(settings, "LLM_API_KEY", None)
            m = model or getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite")
            logger.warning(f"Unknown provider '{prov}', falling back to Gemini ({m})")
            return GeminiProvider(api_key=key, model=m)
