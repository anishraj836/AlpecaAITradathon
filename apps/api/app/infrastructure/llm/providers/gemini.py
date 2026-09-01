import json
import logging
import httpx
from typing import Optional, Type, TypeVar
from pydantic import BaseModel
from app.infrastructure.llm.base import BaseLLMProvider

logger = logging.getLogger("VoltronGeminiProvider")
T = TypeVar("T", bound=BaseModel)

class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini LLM Provider with native structured JSON output schema support.
    Supports gemini-3.6-flash, gemini-3.5-flash-lite, with automatic quota fallback.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key
        self._model = model or "gemini-3.6-flash"
        self._base_url = "https://generativelanguage.googleapis.com/v1beta"

    @property
    def provider_name(self) -> str:
        return "gemini"

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
            logger.debug("Gemini API key not configured. Skipping LLM call.")
            return None

        schema_dict = response_model.model_json_schema()
        full_system = f"{system_instruction}\n\nIMPORTANT: You must output ONLY a valid JSON object matching this schema:\n{json.dumps(schema_dict, indent=2)}"

        payload = {
            "system_instruction": {
                "parts": [{"text": full_system}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
            }
        }

        # Try active model first, fallback to alternate model if 429 quota is reached
        candidate_models = [self._model]
        if "gemini-3.6-flash" not in candidate_models:
            candidate_models.append("gemini-3.6-flash")
        if "gemini-3.5-flash-lite" not in candidate_models:
            candidate_models.append("gemini-3.5-flash-lite")

        for mod in candidate_models:
            url = f"{self._base_url}/models/{mod}:generateContent?key={self._api_key}"
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 429:
                        logger.warning(f"Gemini model {mod} quota exhausted (429). Attempting fallback...")
                        continue
                    if resp.status_code != 200:
                        logger.warning(f"Gemini API ({mod}) returned status {resp.status_code}: {resp.text[:200]}")
                        continue

                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        logger.warning(f"No candidates returned from Gemini ({mod}).")
                        continue

                    content_parts = candidates[0].get("content", {}).get("parts", [])
                    if not content_parts:
                        continue

                    raw_text = content_parts[0].get("text", "").strip()
                    # Remove any markdown codeblocks if model wrapped output in ```json
                    if raw_text.startswith("```"):
                        raw_text = raw_text.split("```json")[-1].split("```")[0].strip()

                    parsed_dict = json.loads(raw_text)
                    logger.info(f"Gemini structured response successfully generated via {mod}.")
                    return response_model.model_validate(parsed_dict)

            except Exception as e:
                logger.warning(f"Gemini generation with {mod} failed: {e}")
                continue

        return None
