import pytest
from app.infrastructure.options.mock_gateway import MockOptionsIntelligenceGateway
from app.domain.models import VolatilitySurface, StrategyCandidate, StressReport, RiskCheckResult

@pytest.mark.asyncio
async def test_get_volatility_surface():
    quant = MockOptionsIntelligenceGateway()
    surface = await quant.get_surface("SPY")
    assert isinstance(surface, VolatilitySurface)
    assert surface.underlying == "SPY"
    assert len(surface.points) > 0
    assert len(surface.termStructure) in (4, 6)
    assert surface.skewSnapshot.skewRatio > 0

@pytest.mark.asyncio
async def test_generate_candidates():
    quant = MockOptionsIntelligenceGateway()
    candidates = await quant.generate_candidates("SPY")
    assert len(candidates) >= 3
    winner = candidates[0]
    assert winner.isWinner is True
    assert winner.score > 60.0
    assert len(winner.legs) in (2, 3, 4)
    # Verify rejected candidate has rejection reason
    rejected = candidates[-1]
    assert rejected.rejectionReason is not None

@pytest.mark.asyncio
async def test_deterministic_risk_compiler():
    quant = MockOptionsIntelligenceGateway()
    candidates = await quant.generate_candidates("SPY")
    winner = candidates[0]
    
    # 1. Normal equity -> should pass
    risk_pass = await quant.compile_risk(winner, portfolio_equity=1245892.12)
    assert isinstance(risk_pass, RiskCheckResult)
    assert risk_pass.isApproved is True
    assert risk_pass.budgetCheck.status == "PASS"
    assert risk_pass.liquidityCheck.status == "PASS"

    # 2. Tiny equity ($100) -> should fail deterministic budget check
    risk_fail = await quant.compile_risk(winner, portfolio_equity=100.0)
    assert risk_fail.isApproved is False
    assert risk_fail.budgetCheck.status == "FAIL"

@pytest.mark.asyncio
async def test_stress_test_matrix():
    quant = MockOptionsIntelligenceGateway()
    stress = await quant.stress_test("strat-condor-01")
    assert isinstance(stress, StressReport)
    assert len(stress.matrix) == 21  # 7 price shifts x 3 IV shifts
    assert stress.maxProfitZone.maxPnl > 0

@pytest.mark.asyncio
async def test_agent_trace():
    quant = MockOptionsIntelligenceGateway()
    steps = await quant.get_agent_trace("DEC-SPY-9942")
    assert len(steps) == 5
    assert steps[0].agentRole == "RESEARCHER"
    assert steps[4].agentRole == "RISK_COMPILER"
