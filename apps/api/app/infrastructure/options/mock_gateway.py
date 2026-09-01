import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure packages/options-alpha-mcp is always discoverable on sys.path
_QUANT_PKG_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "packages" / "options-alpha-mcp"
if _QUANT_PKG_DIR.exists() and str(_QUANT_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_QUANT_PKG_DIR))

try:
    from surface import build_volatility_surface
    from strategies import generate_all_candidate_structures
    from stress import evaluate_strategy_stress
except ImportError:
    pass

from app.infrastructure.options.gateway import OptionsIntelligenceGateway
from app.domain.models import (
    VolatilitySurface,
    VolatilitySurfacePoint,
    TermStructurePoint,
    SkewSnapshot,
    AnomalyReport,
    StrategyCandidate,
    OptionLeg,
    StressReport,
    StressMatrixCell,
    MaxProfitZone,
    ModelAssumptions,
    RiskCheckResult,
    RiskCheckItem,
    AgentTraceStep,
    Tag,
    AgentTraceDetails,
    MetricRow,
    EvaluatedStructure,
    RiskMetric,
    CounterfactualComparison,
    CounterfactualBaseline,
    CounterfactualScenario,
)

class MockOptionsIntelligenceGateway(OptionsIntelligenceGateway):
    """
    Deterministic Development Fixture Mock for Person 2's backend and API layer.
    Allows backend and frontend development to proceed independently before
    Person 1's Options MCP (packages/options-alpha-mcp/) is deployed.
    """

    def _get_demo_strategy(self) -> StrategyCandidate:
        return StrategyCandidate(
            id="strat-condor-01",
            name="Iron Condor",
            underlying="SPY",
            dte=45,
            rank=1,
            isWinner=True,
            score=86.2,
            pop=0.684,
            maxProfit=138.0,
            maxLoss=362.0,
            netCreditOrDebit=1.38,
            liquidityScore=93,
            breakevens=[628.62, 661.38],
            rationale=[
                "Expected to remain range-bound post-earnings season.",
                "Captures volatility skew advantage on both wings.",
                "Strictly defined risk fits current portfolio delta targets.",
            ],
            legs=[
                OptionLeg(
                    id="leg-1",
                    symbol="SPY260918P00625000",
                    underlying="SPY",
                    expiration="2026-09-18",
                    dte=45,
                    strike=625.0,
                    type="PUT",
                    side="BUY",
                    ratio=1,
                    bid=1.08,
                    ask=1.12,
                    mid=1.10,
                    iv=0.284,
                    delta=-0.12,
                    gamma=0.015,
                    theta=-0.04,
                    vega=0.18,
                ),
                OptionLeg(
                    id="leg-2",
                    symbol="SPY260918P00630000",
                    underlying="SPY",
                    expiration="2026-09-18",
                    dte=45,
                    strike=630.0,
                    type="PUT",
                    side="SELL",
                    ratio=1,
                    bid=1.83,
                    ask=1.87,
                    mid=1.85,
                    iv=0.265,
                    delta=-0.16,
                    gamma=0.018,
                    theta=-0.06,
                    vega=0.22,
                ),
                OptionLeg(
                    id="leg-3",
                    symbol="SPY260918C00660000",
                    underlying="SPY",
                    expiration="2026-09-18",
                    dte=45,
                    strike=660.0,
                    type="CALL",
                    side="SELL",
                    ratio=1,
                    bid=1.43,
                    ask=1.47,
                    mid=1.45,
                    iv=0.224,
                    delta=0.18,
                    gamma=0.020,
                    theta=-0.05,
                    vega=0.20,
                ),
                OptionLeg(
                    id="leg-4",
                    symbol="SPY260918C00665000",
                    underlying="SPY",
                    expiration="2026-09-18",
                    dte=45,
                    strike=665.0,
                    type="CALL",
                    side="BUY",
                    ratio=1,
                    bid=0.80,
                    ask=0.84,
                    mid=0.82,
                    iv=0.218,
                    delta=0.10,
                    gamma=0.012,
                    theta=-0.03,
                    vega=0.15,
                ),
            ],
        )

    async def get_surface(
        self,
        symbol: str = "SPY",
        spot: Optional[float] = None,
        chain: Optional[List[Dict[str, Any]]] = None,
    ) -> VolatilitySurface:
        sym = symbol.upper()
        spot_table = {
            "SPY": 645.31,
            "QQQ": 510.00,
            "IWM": 224.50,
            "NVDA": 138.50,
            "AAPL": 228.40,
            "TSLA": 215.10,
            "MSFT": 425.00,
            "AMZN": 186.00,
            "META": 528.00,
            "GOOGL": 168.00,
            "AMD": 154.00,
            "PLTR": 34.50,
            "COIN": 212.00,
            "SMCI": 448.00,
            "ARM": 134.00,
            "GLD": 230.00,
        }
        if spot is not None and spot > 0:
            actual_spot = spot
        elif sym in spot_table:
            actual_spot = spot_table[sym]
        else:
            raise ValueError(f"Ticker '{symbol}' not found on US exchanges. Please enter a valid symbol (e.g. SPY, PLTR, NVDA, TSLA, AAPL).")
        try:
            from surface import build_volatility_surface
            raw_surface = build_volatility_surface(
                underlying=symbol.upper(),
                spot_price=actual_spot,
                change_pct=0.82,
                raw_contracts=chain,
            )
            return VolatilitySurface.model_validate(raw_surface)
        except Exception:
            return VolatilitySurface(
                underlying=symbol.upper(),
                spotPrice=actual_spot,
                changePct=0.82,
                timestamp="10:45:12 AM EST",
                points=[
                    VolatilitySurfacePoint(strike=round(actual_spot * 0.969, 1), dte=14, iv=27.3, delta=-0.15, volume=14200, openInterest=45000),
                    VolatilitySurfacePoint(strike=round(actual_spot * 0.976, 1), dte=14, iv=25.8, delta=-0.22, volume=28400, openInterest=82000),
                    VolatilitySurfacePoint(strike=round(actual_spot * 1.000, 1), dte=14, iv=24.8, delta=0.50, volume=95000, openInterest=180000),
                    VolatilitySurfacePoint(strike=round(actual_spot * 1.023, 1), dte=14, iv=22.4, delta=0.20, volume=34000, openInterest=76000),
                    VolatilitySurfacePoint(strike=round(actual_spot * 1.031, 1), dte=14, iv=21.8, delta=0.12, volume=18500, openInterest=51000),
                ],
                termStructure=[
                    TermStructurePoint(dte=7, label="7D", dateLabel="Nov 24", iv=27.3, percentageOfMax=85.0),
                    TermStructurePoint(dte=14, label="14D", dateLabel="Dec 01", iv=24.8, percentageOfMax=75.0),
                    TermStructurePoint(dte=30, label="30D", dateLabel="Dec 17", iv=23.5, percentageOfMax=65.0),
                    TermStructurePoint(dte=45, label="45D", dateLabel="Jan 01", iv=22.7, percentageOfMax=60.0),
                ],
                skewSnapshot=SkewSnapshot(
                    put25DeltaIV=27.4,
                    atmIV=23.1,
                    call25DeltaIV=21.8,
                    skewRatio=1.25,
                ),
                anomalies=await self.detect_anomalies(symbol),
            )

    async def detect_anomalies(self, symbol: str = "SPY", spot: Optional[float] = None) -> List[AnomalyReport]:
        return [
            AnomalyReport(
                id="anom-1",
                name="PUT SKEW RICH",
                description="Downside protection premium is significantly elevated compared to historical 30-day average.",
                percentile=91.0,
                confidence="HIGH",
                category="SKEW",
                metricLabel="91st %ile",
            ),
            AnomalyReport(
                id="anom-2",
                name="FRONT-END IV ELEV",
                description="7D volatility trading at a premium to longer term structure, indicating near-term event risk pricing.",
                percentile=84.0,
                confidence="MED",
                category="TERM",
                metricLabel="84th %ile",
            ),
            AnomalyReport(
                id="anom-3",
                name="LIQUIDITY SCORE",
                description="Bid-ask spreads are tight across the entire surface. Optimal conditions for complex structure execution.",
                percentile=93.0,
                confidence="HIGH",
                category="LIQUIDITY",
                metricLabel="93/100",
            ),
        ]

    async def generate_candidates(
        self,
        symbol: str = "SPY",
        target_delta: float = 0.15,
        max_budget: float = 50000.0,
        spot: Optional[float] = None,
        chain: Optional[List[Dict[str, Any]]] = None,
    ) -> List[StrategyCandidate]:
        actual_spot = spot if (spot is not None and spot > 0) else (645.31 if symbol.upper() == "SPY" else 230.0)
        try:
            from strategies import generate_all_candidate_structures
            raw_candidates = generate_all_candidate_structures(
                symbol=symbol.upper(),
                spot=actual_spot,
                target_delta=target_delta,
                max_budget=max_budget,
                chain=chain,
            )
            return [StrategyCandidate.model_validate(c) for c in raw_candidates]
        except Exception:
            primary = self._get_demo_strategy()
            return [primary]

    async def stress_test(
        self,
        strategy_id: str = "strat-condor-01",
        spot: Optional[float] = None,
        dte: int = 45,
        legs: Optional[List[Dict[str, Any]]] = None,
        net_credit: float = 1.38,
    ) -> StressReport:
        actual_spot = spot if (spot is not None and spot > 0) else 645.31
        try:
            from stress import evaluate_strategy_stress
            raw_stress = evaluate_strategy_stress(
                strategy_id=strategy_id,
                spot_price=actual_spot,
                dte=dte,
                legs=legs,
                net_credit=net_credit,
            )
            return StressReport.model_validate(raw_stress)
        except Exception:
            return StressReport(
                strategyId=strategy_id,
                modelId="V-CONDOR-09",
                baselinePnl=round(net_credit * 100.0, 2),
                maxProfitZone=MaxProfitZone(minPrice=round(actual_spot * 0.96, 2), maxPrice=round(actual_spot * 1.04, 2), maxPnl=round(net_credit * 100.0, 2)),
                assumptions=ModelAssumptions(
                    riskBudget=50000.0,
                    targetDelta=target_delta if 'target_delta' in locals() else 0.15,
                    evaluationHorizonDays=dte,
                    volRegime="ELEVATED",
                ),
                matrix=[
                    StressMatrixCell(priceShiftPct=-10.0, ivShiftPct=-20.0, pnl=-3620.0),
                    StressMatrixCell(priceShiftPct=-10.0, ivShiftPct=0.0, pnl=-3620.0),
                    StressMatrixCell(priceShiftPct=-10.0, ivShiftPct=20.0, pnl=-3620.0),
                    StressMatrixCell(priceShiftPct=-5.0, ivShiftPct=-20.0, pnl=-2150.0),
                    StressMatrixCell(priceShiftPct=-5.0, ivShiftPct=0.0, pnl=-2850.0),
                    StressMatrixCell(priceShiftPct=-5.0, ivShiftPct=20.0, pnl=-3450.0),
                    StressMatrixCell(priceShiftPct=-3.0, ivShiftPct=-20.0, pnl=720.0),
                    StressMatrixCell(priceShiftPct=-3.0, ivShiftPct=0.0, pnl=-1450.0),
                    StressMatrixCell(priceShiftPct=-3.0, ivShiftPct=20.0, pnl=-3620.0),
                    StressMatrixCell(priceShiftPct=0.0, ivShiftPct=-20.0, pnl=1380.0),
                    StressMatrixCell(priceShiftPct=0.0, ivShiftPct=0.0, pnl=1380.0),
                    StressMatrixCell(priceShiftPct=0.0, ivShiftPct=20.0, pnl=450.0),
                    StressMatrixCell(priceShiftPct=3.0, ivShiftPct=-20.0, pnl=950.0),
                    StressMatrixCell(priceShiftPct=3.0, ivShiftPct=0.0, pnl=-1200.0),
                    StressMatrixCell(priceShiftPct=3.0, ivShiftPct=20.0, pnl=-3450.0),
                    StressMatrixCell(priceShiftPct=5.0, ivShiftPct=-20.0, pnl=-1850.0),
                    StressMatrixCell(priceShiftPct=5.0, ivShiftPct=0.0, pnl=-2600.0),
                    StressMatrixCell(priceShiftPct=5.0, ivShiftPct=20.0, pnl=-3620.0),
                    StressMatrixCell(priceShiftPct=10.0, ivShiftPct=-20.0, pnl=-3620.0),
                    StressMatrixCell(priceShiftPct=10.0, ivShiftPct=0.0, pnl=-3620.0),
                    StressMatrixCell(priceShiftPct=10.0, ivShiftPct=20.0, pnl=-3620.0),
                ],
            )

    async def compile_risk(
        self,
        strategy: StrategyCandidate,
        portfolio_equity: float = 1245892.12,
        uncapped_mode: bool = False,
    ) -> RiskCheckResult:
        # Deterministic pure-code risk rules
        budget_pct = (strategy.maxLoss / portfolio_equity * 100.0) if portfolio_equity else 0.0
        budget_passed = True if uncapped_mode else (budget_pct <= 1.0)
        liquidity_passed = strategy.liquidityScore >= 70

        return RiskCheckResult(
            budgetCheck=RiskCheckItem(
                passed=budget_passed,
                status="PASS" if budget_passed else "FAIL",
                label="Budget Allocation",
                valueText=f"PASS - {budget_pct:.1f}%",
                details=f"Risk allocation of ${strategy.maxLoss:.2f} is {budget_pct:.3f}% of equity (limit 1.0%).",
            ),
            liquidityCheck=RiskCheckItem(
                passed=liquidity_passed,
                status="PASS" if liquidity_passed else "FAIL",
                label="Liquidity Check",
                valueText="PASS" if liquidity_passed else "FAIL",
                details=f"Liquidity score {strategy.liquidityScore}/100 exceeds minimum threshold 70.",
            ),
            concentrationCheck=RiskCheckItem(
                passed=True,
                status="WARN",
                label="Portfolio Concentration",
                valueText="WARN - SPY EXP",
                details="SPY total exposure currently at 34% of portfolio margin.",
            ),
            isApproved=budget_passed and liquidity_passed,
        )

    async def get_agent_trace(self, decision_id: str = "DEC-SPY-9942") -> List[AgentTraceStep]:
        return [
            AgentTraceStep(
                id="step-1",
                agentRole="RESEARCHER",
                agentLabel="Agent 01",
                title="Market Regime Identified",
                timestampOffset="T-45ms",
                status="COMPLETE",
                summary="Identified Range-bound regime with 82% confidence based on compressed 5d realized vol.",
                confidenceScore=0.82,
                tags=[Tag(label="Range-bound", variant="secondary"), Tag(label="82% Conf", variant="tertiary")],
                details=AgentTraceDetails(keyDrivers=["VIX term structure flattened", "SPX 5d realized vol < 12%"]),
            ),
            AgentTraceStep(
                id="step-2",
                agentRole="VOLATILITY_ANALYST",
                agentLabel="Agent 02",
                title="Unusual Put Skew Detected",
                timestampOffset="T-38ms",
                status="COMPLETE",
                summary="25D Put IV trading at 18.4% (91st percentile vs 14.2% mean). Put/call skew ratio at 1.25x.",
                tags=[Tag(label="91st Percentile", variant="error"), Tag(label="30D Expiry", variant="secondary")],
                details=AgentTraceDetails(
                    metrics=[
                        MetricRow(label="25D Put IV", current="18.4%", baseline="14.2%"),
                        MetricRow(label="Skew (25DP - 25DC)", current="4.2 vols", baseline="2.1 vols"),
                    ]
                ),
            ),
            AgentTraceStep(
                id="step-3",
                agentRole="STRATEGY_ANALYST",
                agentLabel="Agent 03",
                title="Candidate #1 Selected (Iron Condor)",
                timestampOffset="T-22ms",
                status="COMPLETE",
                summary="Evaluated 8 structures. Selected Skew-Adjusted Iron Condor with score 86.2.",
                tags=[Tag(label="Iron Condor (Skew-Adjusted)", variant="primary"), Tag(label="8 Structures Evaluated", variant="secondary")],
                details=AgentTraceDetails(
                    evaluatedStructures=[
                        EvaluatedStructure(name="#1: Iron Condor (Asym)", score=86.2, isSelected=True),
                        EvaluatedStructure(name="#2: Broken Wing Butterfly", score=78.4, isSelected=False),
                        EvaluatedStructure(name="#3: Short Put Calendar", score=62.0, isSelected=False),
                    ]
                ),
            ),
            AgentTraceStep(
                id="step-4",
                agentRole="CRITIC",
                agentLabel="Agent 04",
                title="Upside Breakout Risk Identified",
                timestampOffset="T-12ms",
                status="COMPLETE",
                summary="Cautioned on macro CPI upside tail risk. Recommended widening call wing strikes.",
                tags=[Tag(label="Tail Risk Caution", variant="error")],
                details=AgentTraceDetails(recommendations=["Shift call wing strikes up by 1 standard deviation (Delta reduced to -0.05)."]),
            ),
            AgentTraceStep(
                id="step-5",
                agentRole="RISK_COMPILER",
                agentLabel="Deterministic Code Check",
                title="Final Checks Passed",
                timestampOffset="T-0ms (READY)",
                status="COMPLETE",
                summary="Budget 0.029%, liquidity tight, portfolio concentration bounded. Pure code gate cleared.",
                tags=[Tag(label="APPROVED FOR EXECUTION", variant="primary")],
                details=AgentTraceDetails(
                    riskMetrics=[
                        RiskMetric(label="Margin Impact", value="$12,500"),
                        RiskMetric(label="Max Loss", value="$362"),
                        RiskMetric(label="Est. Credit", value="$138"),
                        RiskMetric(label="Win Prob", value="68.4%"),
                    ]
                ),
            ),
        ]

    async def get_counterfactual(
        self,
        params: Optional[Dict[str, Any]] = None,
    ) -> CounterfactualComparison:
        params = params or {}
        strat = self._get_demo_strategy()
        return CounterfactualComparison(
            baseline=CounterfactualBaseline(
                targetDelta=25.0,
                dteDays=45,
                allocatedBudget=1000.0,
                winningStrategy=strat,
            ),
            scenario=CounterfactualScenario(
                targetDelta=float(params.get("targetDelta", 15.0)),
                dteDays=int(params.get("dteDays", 30)),
                allocatedBudget=float(params.get("budget", 2500.0)),
                winningStrategy=StrategyCandidate(
                    id="strat-condor-12",
                    name="Iron Condor #12 (Wide Wings)",
                    underlying="SPY",
                    dte=int(params.get("dteDays", 30)),
                    score=88.7,
                    pop=0.76,
                    maxProfit=850.0,
                    maxLoss=1650.0,
                    netCreditOrDebit=8.50,
                    liquidityScore=91,
                    breakevens=[618.5, 671.5],
                    legs=[],
                ),
                reasoning=[
                    "Increased budget allows for multi-leg Iron Condor structures with higher margin requirements.",
                    "Delta 15 shift pushed optimal strikes wider, favoring defined risk spreads.",
                    "Shorter DTE (30D) increased gamma risk, reducing Iron Condor viability.",
                ],
            ),
        )
