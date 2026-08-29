from fastapi import APIRouter, Depends
from app.api.deps import get_broker_gateway, get_quant_gateway
from app.services.market_service import MarketService
from app.domain.models import TelemetryStatus

router = APIRouter(tags=["Telemetry"])

@router.get("/telemetry", response_model=TelemetryStatus)
async def get_telemetry(
    symbol: str = "SPY",
    broker_gw = Depends(get_broker_gateway),
    quant_gw = Depends(get_quant_gateway),
):
    service = MarketService(broker_gw, quant_gw)
    return await service.get_telemetry(symbol)
