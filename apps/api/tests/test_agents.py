import pytest
from app.agents.researcher import MarketResearcherAgent
from app.agents.volatility import VolatilityAnalystAgent
from app.agents.strategist import StrategyAnalystAgent, StrategyAnalystInput
from app.agents.critic import CriticAgent, CriticInput
from app.domain.models import MarketContext, VolatilitySurface, StrategyCandidate, StressReport
from app.infrastructure.options.mock_gateway import MockOptionsIntelligenceGateway

@pytest.mark.asyncio
async def test_researcher_agent():
    agent = MarketResearcherAgent()
    context = MarketContext(
        symbol="SPY",
        price=645.31,
        changePct=0.45,
        high=647.2,
        low=643.1,
        volume=85000000,
        timestamp="2026-08-29T10:00:00Z",
    )
    research, trace = await agent.run(context, decision_id="DEC-TEST", step_id="step-1", title="Market Context")
    assert research.symbol == "SPY"
    assert research.spotPrice == 645.31
    assert len(research.marketRegimeSummary) > 0
    assert research.confidence >= 0.5
    assert trace.agentRole == "RESEARCHER"
    assert trace.status == "COMPLETE"

@pytest.mark.asyncio
async def test_volatility_analyst_agent():
    agent = VolatilityAnalystAgent()
    quant = MockOptionsIntelligenceGateway()
    surface = await quant.get_surface("SPY")
    vol_out, trace = await agent.run(surface, decision_id="DEC-TEST", step_id="step-2", title="Volatility Analysis")
    assert vol_out.symbol == "SPY"
    assert len(vol_out.skewInterpretation) > 0
    assert vol_out.confidence >= 0.5
    assert trace.agentRole == "VOLATILITY_ANALYST"
    assert trace.status == "COMPLETE"

@pytest.mark.asyncio
async def test_strategy_analyst_agent_valid():
    agent = StrategyAnalystAgent()
    quant = MockOptionsIntelligenceGateway()
    candidates = await quant.generate_candidates("SPY")
    
    # Fake research and volatility
    research_agent = MarketResearcherAgent()
    vol_agent = VolatilityAnalystAgent()
    surface = await quant.get_surface("SPY")
    
    ctx = MarketContext(symbol="SPY", price=645.31, changePct=0.45, high=647.0, low=643.0, volume=80000000, timestamp="2026-08-29T10:00:00Z")
    research, _ = await research_agent.run(ctx, "DEC-TEST", "s1", "Research")
    vol_out, _ = await vol_agent.run(surface, "DEC-TEST", "s2", "Vol")

    strat_in = StrategyAnalystInput(research=research, volatility=vol_out, candidates=candidates)
    strat_out, trace = await agent.run(strat_in, "DEC-TEST", "s3", "Strategy Selection")

    assert strat_out.selectedCandidateId in [c.id for c in candidates]
    assert len(strat_out.reasoning) >= 1
    assert trace.agentRole == "STRATEGY_ANALYST"

@pytest.mark.asyncio
async def test_strategy_analyst_empty_candidates_fails():
    agent = StrategyAnalystAgent()
    research_agent = MarketResearcherAgent()
    vol_agent = VolatilityAnalystAgent()
    quant = MockOptionsIntelligenceGateway()
    surface = await quant.get_surface("SPY")
    ctx = MarketContext(symbol="SPY", price=645.31, changePct=0.45, high=647.0, low=643.0, volume=80000000, timestamp="2026-08-29T10:00:00Z")
    research, _ = await research_agent.run(ctx, "DEC-TEST", "s1", "Research")
    vol_out, _ = await vol_agent.run(surface, "DEC-TEST", "s2", "Vol")

    strat_in = StrategyAnalystInput(research=research, volatility=vol_out, candidates=[])
    with pytest.raises(ValueError, match="empty candidate set"):
        await agent.run(strat_in, "DEC-TEST", "s3", "Strategy Selection")

@pytest.mark.asyncio
async def test_critic_agent():
    agent = CriticAgent()
    quant = MockOptionsIntelligenceGateway()
    strat = (await quant.generate_candidates("SPY"))[0]
    stress = await quant.stress_test(strat.id)

    research_agent = MarketResearcherAgent()
    vol_agent = VolatilityAnalystAgent()
    surface = await quant.get_surface("SPY")
    ctx = MarketContext(symbol="SPY", price=645.31, changePct=0.45, high=647.0, low=643.0, volume=80000000, timestamp="2026-08-29T10:00:00Z")
    research, _ = await research_agent.run(ctx, "DEC-TEST", "s1", "Research")
    vol_out, _ = await vol_agent.run(surface, "DEC-TEST", "s2", "Vol")

    critic_in = CriticInput(strategy=strat, stressReport=stress, research=research, volatility=vol_out)
    critique, trace = await agent.run(critic_in, "DEC-TEST", "s4", "Adversarial Critique")

    assert critique.verdict in ["APPROVED_WITH_CONDITIONS", "APPROVED", "REJECTED"]
    assert "corridor" in critique.primaryFailureMode.lower()
    assert len(critique.failureScenarios) > 0
    assert trace.agentRole == "CRITIC"
