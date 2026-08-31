from typing import List, Optional, Dict, Any
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
        spot: Optional[float] = None,
        chain: Optional[List[Dict[str, Any]]] = None,
    ) -> List[StrategyCandidate]:
        return await self.quant_gateway.generate_candidates(
            symbol=symbol,
            target_delta=target_delta,
            max_budget=budget,
            spot=spot,
            chain=chain,
        )
