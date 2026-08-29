from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
async def get_health():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": "paper" if settings.ALPACA_PAPER else "live",
        "quant_mode": "mock_adapter" if settings.USE_MOCK_QUANT else "voltron_mcp",
    }
