import json
import logging
import httpx
from typing import Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel
from app.infrastructure.llm.base import BaseLLMProvider

logger = logging.getLogger("VoltronOpenAICompatibleProvider")
T = TypeVar("T", bound=BaseModel)

class OpenAICompatibleProvider(BaseLLMProvider):
    """
    Generic OpenAI-compatible Provider supporting:
    - OpenAI (https://api.openai.com/v1)
    - Groq (https://api.groq.com/openai/v1)
    - DeepSeek (https://api.deepseek.com/v1)
    - OpenRouter (https://openrouter.ai/api/v1)
    - Together AI / Mistral / Perplexity / vLLM / LMStudio
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        provider_name: str = "openai",
    ):
        self._api_key = api_key
        self._model = model or "gpt-4o-mini"
        self._base_url = (base_url or "https://api.openai.com/v1").rstrip("/")
        self._provider_name = provider_name

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def is_configured(self) -> bool:
        # If local URL (e.g. localhost/127.0.0.1), API key can be optional
        if "localhost" in self._base_url or "127.0.0.1" in self._base_url:
            return True
        return bool(self._api_key and not self._api_key.startswith("DUMMY") and len(self._api_key) > 5)

    async def generate_structured(
        self,
        system_instruction: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.2,
    ) -> Optional[T]:
        if not self.is_configured:
            logger.debug(f"{self._provider_name} API key not configured. Skipping LLM call.")
            return None

        url = f"{self._base_url}/chat/completions"
        schema_dict = response_model.model_json_schema()
        full_system = (
            f"{system_instruction}\n\n"
            f"CRITICAL REQUIREMENT: Output strictly a valid JSON object adhering to this schema:\n"
            f"{json.dumps(schema_dict, indent=2)}\n"
            f"Do not include markdown tags, codeblocks, or conversational prefixes. Output raw JSON only."
        )

        headers: Dict[str, str] = {
            "Content-Type": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": full_system},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.warning(f"{self._provider_name} returned status {resp.status_code}: {resp.text[:300]}")
                    return None

                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    return None

                raw_content = choices[0].get("message", {}).get("content", "").strip()
                if raw_content.startswith("```"):
                    raw_content = raw_content.split("```json")[-1].split("```")[0].strip()

                parsed_dict = json.loads(raw_content)
                return response_model.model_validate(parsed_dict)

        except Exception as e:
            logger.warning(f"{self._provider_name} structured generation failed: {e}")
            return None
