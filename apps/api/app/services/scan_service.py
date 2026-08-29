from typing import List
from app.infrastructure.options.gateway import OptionsIntelligenceGateway
from app.domain.models import StrategyCandidate

class ScanService:
    def __init__(self, quant_gateway: OptionsIntelligenceGateway):
        self.quant_gateway = quant_gateway

    async def run_strategy_tournament(
        self,
        symbol: str = "SPY",
        target_delta: float = 0.15,
        budget: float = 50000.0,
    ) -> List[StrategyCandidate]:
        return await self.quant_gateway.generate_candidates(symbol, target_delta, budget)
