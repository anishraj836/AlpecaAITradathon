from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.domain.models import (
    VolatilitySurface,
    AnomalyReport,
    StrategyCandidate,
    StressReport,
    RiskCheckResult,
    AgentTraceStep,
    CounterfactualComparison,
)

class OptionsIntelligenceGateway(ABC):
    """
    Gateway interface to Person 1's Options Intelligence MCP (packages/options-alpha-mcp/).
    Person 1 owns all canonical quantitative models: surface math, skew calculus,
    strategy generation, scoring, stress test, and deterministic risk compilation.
    """

    @abstractmethod
    async def get_surface(
        self,
        symbol: str,
        spot: Optional[float] = None,
        chain: Optional[List[Dict[str, Any]]] = None,
    ) -> VolatilitySurface:
        """Compute the implied volatility surface, term structure, and skew snapshot."""
        pass

    @abstractmethod
    async def detect_anomalies(self, symbol: str, spot: Optional[float] = None) -> List[AnomalyReport]:
        """Scan volatility surface for statistical anomalies and skew dislocations."""
        pass

    @abstractmethod
    async def generate_candidates(
        self,
        symbol: str,
        target_delta: float = 0.15,
        max_budget: float = 50000.0,
        spot: Optional[float] = None,
        chain: Optional[List[Dict[str, Any]]] = None,
    ) -> List[StrategyCandidate]:
        """Generate multi-leg defined-risk strategy candidates matching the thesis."""
        pass

    @abstractmethod
    async def stress_test(
        self,
        strategy_id: str,
        spot: Optional[float] = None,
        dte: int = 45,
        legs: Optional[List[Dict[str, Any]]] = None,
        net_credit: float = 1.38,
    ) -> StressReport:
        """Run multi-scenario price vs IV stress test matrix for a candidate strategy."""
        pass

    @abstractmethod
    async def compile_risk(
        self,
        strategy: StrategyCandidate,
        portfolio_equity: float,
        uncapped_mode: bool = False,
    ) -> RiskCheckResult:
        """
        Execute deterministic pure-code risk compiler checks (budget, liquidity, concentration).
        Note: This is deterministic code, NOT an LLM agent.
        """
        pass

    @abstractmethod
    async def get_agent_trace(self, decision_id: str) -> List[AgentTraceStep]:
        """Retrieve multi-agent deliberation and consensus timeline."""
        pass

    @abstractmethod
    async def get_counterfactual(
        self,
        params: Optional[Dict[str, Any]] = None,
    ) -> CounterfactualComparison:
        """Evaluate sensitivity and counterfactual shifts for different parameter constraints."""
        pass
