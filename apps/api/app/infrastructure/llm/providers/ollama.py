import json
import logging
import httpx
from typing import Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel
from app.infrastructure.llm.base import BaseLLMProvider

logger = logging.getLogger("VoltronOllamaProvider")
T = TypeVar("T", bound=BaseModel)

class OllamaProvider(BaseLLMProvider):
    """
    Local Ollama Provider (llama3.2, qwen2.5, mistral, deepseek-r1).
    Runs 100% offline with zero cost on local GPU / Apple Silicon.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self._base_url = (base_url or "http://localhost:11434").rstrip("/")
        self._model = model or "llama3.2:3b"

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def is_configured(self) -> bool:
        return True # Ollama does not require API keys

    async def generate_structured(
        self,
        system_instruction: str,
        user_prompt: str,
        response_model: Type[T],
        temperature: float = 0.2,
    ) -> Optional[T]:
        url = f"{self._base_url}/api/generate"
        schema_dict = response_model.model_json_schema()
        full_prompt = (
            f"{system_instruction}\n\n"
            f"SCHEMA:\n{json.dumps(schema_dict, indent=2)}\n\n"
            f"USER INPUT:\n{user_prompt}\n\n"
            f"Output strictly valid JSON matching the schema."
        )

        payload: Dict[str, Any] = {
            "model": self._model,
            "prompt": full_prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    logger.debug(f"Ollama returned status {resp.status_code}: {resp.text[:200]}")
                    return None

                data = resp.json()
                raw_response = data.get("response", "").strip()
                if raw_response.startswith("```"):
                    raw_response = raw_response.split("```json")[-1].split("```")[0].strip()

                parsed_dict = json.loads(raw_response)
                return response_model.model_validate(parsed_dict)

        except Exception as e:
            logger.debug(f"Ollama local inference unavailable: {e}")
            return None
