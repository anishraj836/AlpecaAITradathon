from datetime import datetime, timezone
from app.infrastructure.alpaca.gateway import BrokerGateway
from app.infrastructure.options.gateway import OptionsIntelligenceGateway
from app.domain.models import TelemetryStatus

def _now_est_str() -> str:
    return datetime.now(timezone.utc).strftime("%I:%M:%S %p EST")

class MarketService:
    def __init__(self, broker_gateway: BrokerGateway, quant_gateway: OptionsIntelligenceGateway):
        self.broker_gateway = broker_gateway
        self.quant_gateway = quant_gateway

    async def get_telemetry(self, symbol: str = "SPY") -> TelemetryStatus:
        account = await self.broker_gateway.get_account()
        context = await self.broker_gateway.get_market_context(symbol)

        return TelemetryStatus(
            marketStatus="OPEN",
            underlying=symbol.upper(),
            underlyingPrice=context.price,
            underlyingChangePct=context.changePct,
            accountEquity=account.equity,
            buyingPower=account.buyingPower,
            alpacaConnected=True,
            isPaper=account.isPaper,
            timestamp=_now_est_str(),
        )
