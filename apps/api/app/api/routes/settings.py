import time
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import settings
from app.infrastructure.llm import llm_client, LLMFactory
from app.domain.models import (
    SystemSettings,
    UpdateSettingsRequest,
    TestConnectionRequest,
    TestConnectionResponse,
)

logger = logging.getLogger("VoltronSettingsRoute")
router = APIRouter(prefix="/api/settings", tags=["Settings"])

class PingSchema(BaseModel):
    status: str
    reply: str

@router.get("", response_model=SystemSettings)
async def get_system_settings():
    """Retrieve active LLM Provider, Model, and Autonomy configurations."""
    active_prov = llm_client.provider_name
    active_mod = llm_client.model_name
    is_configured = llm_client.is_configured
    
    # Mask API key if configured
    masked_key = "••••••••••••••••••••" if is_configured else None

    return SystemSettings(
        llmProvider=active_prov,
        llmModel=active_mod,
        isApiKeyConfigured=is_configured,
        apiKeyMasked=masked_key,
        autonomyLevel=getattr(settings, "AUTONOMY_LEVEL", "GUARDED_AUTONOMOUS"),
    )

@router.post("", response_model=SystemSettings)
async def update_system_settings(req: UpdateSettingsRequest):
    """Update LLM Provider, Model, API Key, and Autonomy Level at runtime."""
    try:
        if req.autonomyLevel:
            setattr(settings, "AUTONOMY_LEVEL", req.autonomyLevel)
            # Update autonomous execution flag
            if req.autonomyLevel == "COPILOT":
                setattr(settings, "AUTONOMOUS_EXECUTION", False)
            else:
                setattr(settings, "AUTONOMOUS_EXECUTION", True)

        prov = req.llmProvider or llm_client.provider_name
        mod = req.llmModel or llm_client.model_name
        key = req.apiKey

        llm_client.reload_provider(
            provider=prov,
            model=mod,
            api_key=key,
            base_url=req.baseUrl,
        )

        logger.info(f"Updated System Settings: Provider={llm_client.provider_name}, Model={llm_client.model_name}")
        return await get_system_settings()

    except Exception as e:
        logger.error(f"Failed to update settings: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/test", response_model=TestConnectionResponse)
async def test_llm_connection(req: TestConnectionRequest):
    """Test connectivity and schema generation with a chosen LLM provider."""
    start_t = time.perf_counter()
    try:
        provider = LLMFactory.create_provider(
            provider=req.provider,
            model=req.model,
            api_key=req.apiKey,
            base_url=req.baseUrl,
        )

        if not provider.is_configured:
            return TestConnectionResponse(
                success=False,
                provider=req.provider,
                model=provider.model_name,
                message="Provider requires a valid API key.",
            )

        # Quick test generation
        res = await provider.generate_structured(
            system_instruction="You are a ping test assistant. Reply with valid JSON.",
            user_prompt="Say pong.",
            response_model=PingSchema,
        )
        latency = int((time.perf_counter() - start_t) * 1000)

        if res and res.reply:
            return TestConnectionResponse(
                success=True,
                provider=req.provider,
                model=provider.model_name,
                message=f"Connected successfully ({latency}ms)! Model responded: '{res.reply}'",
                latencyMs=latency,
            )
        else:
            return TestConnectionResponse(
                success=False,
                provider=req.provider,
                model=provider.model_name,
                message="Model returned empty response or invalid schema.",
                latencyMs=latency,
            )

    except Exception as e:
        latency = int((time.perf_counter() - start_t) * 1000)
        return TestConnectionResponse(
            success=False,
            provider=req.provider,
            model=req.model or "unknown",
            message=f"Connection failed: {str(e)}",
            latencyMs=latency,
        )
