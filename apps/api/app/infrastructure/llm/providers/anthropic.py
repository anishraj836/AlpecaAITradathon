import json
import logging
import httpx
from typing import Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel
from app.infrastructure.llm.base import BaseLLMProvider

logger = logging.getLogger("VoltronAnthropicProvider")
T = TypeVar("T", bound=BaseModel)

class AnthropicProvider(BaseLLMProvider):
    """
    Anthropic Claude Provider (claude-3-5-sonnet, claude-3-5-haiku, claude-3-opus).
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key
        self._model = model or "claude-3-5-haiku-20241022"
        self._base_url = "https://api.anthropic.com/v1"

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key and not self._api_key.startswith("DUMMY") and len(self._api_key) > 5)

    async def generate_structured(
        self,
        system_instruction: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.2,
    ) -> Optional[T]:
        if not self.is_configured:
            logger.debug("Anthropic API key not configured. Skipping LLM call.")
            return None

        url = f"{self._base_url}/messages"
        schema_dict = response_model.model_json_schema()
        full_system = (
            f"{system_instruction}\n\n"
            f"CRITICAL REQUIREMENT: Output strictly a valid JSON object adhering to this schema:\n"
            f"{json.dumps(schema_dict, indent=2)}\n"
            f"Do not include explanation, thinking, markdown code blocks, or text outside the JSON. Start your answer directly with {{"
        )

        headers: Dict[str, str] = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": self._model,
            "max_tokens": 4096,
            "system": full_system,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code != 200:
                    logger.warning(f"Anthropic API returned status {resp.status_code}: {resp.text[:300]}")
                    return None

                data = resp.json()
                content_blocks = data.get("content", [])
                if not content_blocks:
                    return None

                raw_content = content_blocks[0].get("text", "").strip()
                if raw_content.startswith("```"):
                    raw_content = raw_content.split("```json")[-1].split("```")[0].strip()

                parsed_dict = json.loads(raw_content)
                return response_model.model_validate(parsed_dict)

        except Exception as e:
            logger.warning(f"Anthropic structured generation failed: {e}")
            return None
