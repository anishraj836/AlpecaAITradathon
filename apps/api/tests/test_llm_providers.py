import pytest
from pydantic import BaseModel
from app.infrastructure.llm.base import BaseLLMProvider
from app.infrastructure.llm.factory import LLMFactory
from app.infrastructure.llm.client import LLMClient
from app.infrastructure.llm.providers.gemini import GeminiProvider
from app.infrastructure.llm.providers.openai_compatible import OpenAICompatibleProvider
from app.infrastructure.llm.providers.anthropic import AnthropicProvider
from app.infrastructure.llm.providers.ollama import OllamaProvider
from app.infrastructure.gemini.client import gemini_client, GeminiClient
from app.domain.models import MarketResearch, VolatilityAnalysis, StrategySelection, Critique

class SampleSchema(BaseModel):
    name: str
    confidence: float

def test_llm_factory_instantiation():
    # Gemini
    p_gemini = LLMFactory.create_provider("gemini", api_key="dummy_key", model="gemini-3.5-flash-lite")
    assert isinstance(p_gemini, GeminiProvider)
    assert p_gemini.provider_name == "gemini"
    assert p_gemini.model_name == "gemini-3.5-flash-lite"

    # OpenAI
    p_openai = LLMFactory.create_provider("openai", api_key="sk-test", model="gpt-4o")
    assert isinstance(p_openai, OpenAICompatibleProvider)
    assert p_openai.provider_name == "openai"
    assert p_openai.model_name == "gpt-4o"

    # Groq
    p_groq = LLMFactory.create_provider("groq", api_key="gsk-test", model="llama-3.3-70b-versatile")
    assert isinstance(p_groq, OpenAICompatibleProvider)
    assert p_groq.provider_name == "groq"
    assert p_groq.model_name == "llama-3.3-70b-versatile"

    # Anthropic
    p_anthropic = LLMFactory.create_provider("anthropic", api_key="sk-ant-test", model="claude-3-5-sonnet")
    assert isinstance(p_anthropic, AnthropicProvider)
    assert p_anthropic.provider_name == "anthropic"
    assert p_anthropic.model_name == "claude-3-5-sonnet"

    # DeepSeek
    p_deepseek = LLMFactory.create_provider("deepseek", api_key="sk-deep-test", model="deepseek-chat")
    assert isinstance(p_deepseek, OpenAICompatibleProvider)
    assert p_deepseek.provider_name == "deepseek"
    assert p_deepseek.model_name == "deepseek-chat"

    # Ollama Local
    p_ollama = LLMFactory.create_provider("ollama", model="llama3.2:3b")
    assert isinstance(p_ollama, OllamaProvider)
    assert p_ollama.provider_name == "ollama"
    assert p_ollama.model_name == "llama3.2:3b"

def test_llm_client_runtime_switching():
    client = LLMClient()
    assert client.provider is not None

    # Switch to OpenAI
    client.reload_provider(provider="openai", model="gpt-4o-mini", api_key="sk-test-123")
    assert client.provider_name == "openai"
    assert client.model_name == "gpt-4o-mini"
    assert client.is_configured is True

    # Switch to Groq
    client.reload_provider(provider="groq", model="llama-3.1-8b-instant", api_key="gsk-test-456")
    assert client.provider_name == "groq"
    assert client.model_name == "llama-3.1-8b-instant"

    # Switch to Anthropic
    client.reload_provider(provider="anthropic", model="claude-3-5-haiku", api_key="sk-ant-789")
    assert client.provider_name == "anthropic"
    assert client.model_name == "claude-3-5-haiku"

    # Switch to Ollama
    client.reload_provider(provider="ollama", model="qwen2.5:3b")
    assert client.provider_name == "ollama"
    assert client.model_name == "qwen2.5:3b"

def test_gemini_shim_backwards_compatibility():
    assert gemini_client is not None
    assert isinstance(GeminiClient(), LLMClient)

@pytest.mark.asyncio
async def test_unconfigured_provider_graceful_fallback():
    # Unconfigured OpenAI provider should return None without crashing
    p_unconfigured = OpenAICompatibleProvider(api_key=None, model="gpt-4o")
    res = await p_unconfigured.generate_structured("Instruction", "User prompt", SampleSchema)
    assert res is None
