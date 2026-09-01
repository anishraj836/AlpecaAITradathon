import httpx
from typing import List, Dict, Any, Optional
from app.config import settings
from app.infrastructure.options.gateway import OptionsIntelligenceGateway
from app.infrastructure.options.mock_gateway import MockOptionsIntelligenceGateway
from app.domain.models import (
    VolatilitySurface,
    AnomalyReport,
    StrategyCandidate,
    StressReport,
    RiskCheckResult,
    AgentTraceStep,
    CounterfactualComparison,
)

class VoltronOptionsMCPClient(OptionsIntelligenceGateway):
    """
    HTTP / JSON-RPC 2.0 Client connecting to Person 1's Options Intelligence MCP
    located at packages/options-alpha-mcp/.
    Falls back gracefully to MockOptionsIntelligenceGateway if server is offline or in development.
    """

    def __init__(self):
        self.mock_fallback = MockOptionsIntelligenceGateway()
        self.base_url = settings.VOLTRON_MCP_URL

    async def get_surface(
        self,
        symbol: str,
        spot: Optional[float] = None,
        chain: Optional[List[Dict[str, Any]]] = None,
    ) -> VolatilitySurface:
        if settings.USE_MOCK_QUANT or not self.base_url:
            return await self.mock_fallback.get_surface(symbol, spot=spot, chain=chain)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/rpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "get_surface",
                        "params": {"symbol": symbol, "spot": spot, "chain": chain},
                        "id": 1,
                    },
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    result = resp.json().get("result")
                    if result:
                        return VolatilitySurface.model_validate(result)
        except Exception:
            pass
        return await self.mock_fallback.get_surface(symbol, spot=spot, chain=chain)

    async def detect_anomalies(self, symbol: str, spot: Optional[float] = None) -> List[AnomalyReport]:
        if settings.USE_MOCK_QUANT or not self.base_url:
            return await self.mock_fallback.detect_anomalies(symbol, spot=spot)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/rpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "detect_anomalies",
                        "params": {"symbol": symbol, "spot": spot},
                        "id": 2,
                    },
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    result = resp.json().get("result")
                    if result:
                        return [AnomalyReport.model_validate(item) for item in result]
        except Exception:
            pass
        return await self.mock_fallback.detect_anomalies(symbol, spot=spot)

    async def generate_candidates(
        self,
        symbol: str,
        target_delta: float = 0.15,
        max_budget: float = 50000.0,
        spot: Optional[float] = None,
        chain: Optional[List[Dict[str, Any]]] = None,
    ) -> List[StrategyCandidate]:
        if settings.USE_MOCK_QUANT or not self.base_url:
            return await self.mock_fallback.generate_candidates(
                symbol, target_delta, max_budget, spot=spot, chain=chain
            )
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/rpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "generate_candidates",
                        "params": {
                            "symbol": symbol,
                            "target_delta": target_delta,
                            "max_budget": max_budget,
                            "spot": spot,
                            "chain": chain,
                        },
                        "id": 3,
                    },
                    timeout=15.0,
                )
                if resp.status_code == 200:
                    result = resp.json().get("result")
                    if result:
                        return [StrategyCandidate.model_validate(item) for item in result]
        except Exception:
            pass
        return await self.mock_fallback.generate_candidates(
            symbol, target_delta, max_budget, spot=spot, chain=chain
        )

    async def stress_test(
        self,
        strategy_id: str,
        spot: Optional[float] = None,
        dte: int = 45,
        legs: Optional[List[Dict[str, Any]]] = None,
        net_credit: float = 1.38,
    ) -> StressReport:
        if settings.USE_MOCK_QUANT or not self.base_url:
            return await self.mock_fallback.stress_test(
                strategy_id, spot=spot, dte=dte, legs=legs, net_credit=net_credit
            )
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/rpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "stress_test",
                        "params": {
                            "strategy_id": strategy_id,
                            "spot": spot,
                            "dte": dte,
                            "legs": legs,
                            "net_credit": net_credit,
                        },
                        "id": 4,
                    },
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    result = resp.json().get("result")
                    if result:
                        return StressReport.model_validate(result)
        except Exception:
            pass
        return await self.mock_fallback.stress_test(
            strategy_id, spot=spot, dte=dte, legs=legs, net_credit=net_credit
        )

    async def compile_risk(
        self,
        strategy: StrategyCandidate,
        portfolio_equity: float,
        uncapped_mode: bool = False,
    ) -> RiskCheckResult:
        if settings.USE_MOCK_QUANT or not self.base_url:
            return await self.mock_fallback.compile_risk(strategy, portfolio_equity, uncapped_mode=uncapped_mode)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/rpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "compile_risk",
                        "params": {
                            "strategy": strategy.model_dump(),
                            "portfolio_equity": portfolio_equity,
                            "uncapped_mode": uncapped_mode,
                        },
                        "id": 5,
                    },
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    result = resp.json().get("result")
                    if result:
                        return RiskCheckResult.model_validate(result)
        except Exception:
            pass
        return await self.mock_fallback.compile_risk(strategy, portfolio_equity, uncapped_mode=uncapped_mode)

    async def get_agent_trace(self, decision_id: str) -> List[AgentTraceStep]:
        return await self.mock_fallback.get_agent_trace(decision_id)

    async def get_counterfactual(
        self,
        params: Optional[Dict[str, Any]] = None,
    ) -> CounterfactualComparison:
        if settings.USE_MOCK_QUANT or not self.base_url:
            return await self.mock_fallback.get_counterfactual(params)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.base_url}/rpc",
                    json={
                        "jsonrpc": "2.0",
                        "method": "get_counterfactual",
                        "params": {"params": params or {}},
                        "id": 6,
                    },
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    result = resp.json().get("result")
                    if result:
                        return CounterfactualComparison.model_validate(result)
        except Exception:
            pass
        return await self.mock_fallback.get_counterfactual(params)
