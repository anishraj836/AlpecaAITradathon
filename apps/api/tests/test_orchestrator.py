import pytest
from app.agents.orchestrator import VoltronOrchestrator
from app.infrastructure.alpaca.mcp_client import AlpacaBrokerGateway
from app.infrastructure.options.mock_gateway import MockOptionsIntelligenceGateway
from app.infrastructure.database.session import async_session_factory
from app.infrastructure.database.repositories.decisions import DecisionRepository
from app.infrastructure.database.repositories.agents import AgentRepository
from app.infrastructure.database.repositories.risk import RiskRepository
from app.infrastructure.database.repositories.strategies import StrategyRepository

@pytest.mark.asyncio
async def test_orchestrator_end_to_end():
    broker = AlpacaBrokerGateway()
    quant = MockOptionsIntelligenceGateway()

    async with async_session_factory() as session:
        orchestrator = VoltronOrchestrator(
            broker_gateway=broker,
            quant_gateway=quant,
            session=session,
        )

        packet = await orchestrator.execute_mandate(
            mandate="Harvest elevated 30-day SPY put skew with defined risk",
            symbol="SPY",
        )

        # 1. Assert Packet Structure
        assert packet.id.startswith("DEC-SPY-")
        assert packet.underlying == "SPY"
        assert packet.strategy.name in ("Iron Condor", "Put Credit Spread")
        assert packet.strategy.isWinner is True
        assert len(packet.strategy.legs) in (2, 4)
        assert packet.riskCompilerResult.isApproved is True
        assert packet.status in ("APPROVED", "AWAITING_APPROVAL")
        assert packet.aiConfidence > 0
        assert packet.autonomyLevel is not None

        # 2. Assert Persistence in Database
        dec_repo = DecisionRepository(session)
        agent_repo = AgentRepository(session)
        risk_repo = RiskRepository(session)
        strat_repo = StrategyRepository(session)

        db_dec = await dec_repo.get_by_id(packet.id)
        assert db_dec is not None
        assert db_dec.status in ("APPROVED", "AWAITING_APPROVAL")

        agent_runs = await agent_repo.get_by_decision(packet.id)
        assert len(agent_runs) == 5  # Researcher, Vol Analyst, Strategy Analyst, Critic, Risk Compiler

        risk_check = await risk_repo.get_by_decision(packet.id)
        assert risk_check is not None
        assert risk_check.is_approved is True

        strat_candidates = await strat_repo.get_by_decision(packet.id)
        assert len(strat_candidates) >= 3

@pytest.mark.asyncio
async def test_orchestrator_no_trade_path():
    broker = AlpacaBrokerGateway()
    quant = MockOptionsIntelligenceGateway()

    # Create a custom mock quant that fails risk checks
    class FailingRiskQuant(MockOptionsIntelligenceGateway):
        async def compile_risk(self, strategy, portfolio_equity):
            res = await super().compile_risk(strategy, portfolio_equity)
            res.isApproved = False
            res.budgetCheck.passed = False
            res.budgetCheck.status = "FAIL"
            return res

    async with async_session_factory() as session:
        orchestrator = VoltronOrchestrator(
            broker_gateway=broker,
            quant_gateway=FailingRiskQuant(),
            session=session,
        )

        packet = await orchestrator.execute_mandate(
            mandate="Risky trade mandate",
            symbol="SPY",
        )

        # Assert NO-TRADE / REJECTED status
        assert packet.riskCompilerResult.isApproved is False
        assert packet.status == "REJECTED"

@pytest.mark.asyncio
async def test_orchestrator_market_closed_held(monkeypatch):
    """
    Verify that in autonomous mode, when the market is closed,
    the orchestrator generates the decision but safely holds it in AWAITING_APPROVAL
    rather than dispatching a doomed order to Alpaca.
    """
    broker = AlpacaBrokerGateway()
    quant = MockOptionsIntelligenceGateway()

    # Mock market clock as CLOSED
    async def mock_get_clock():
        return {
            "is_open": False,
            "next_open": "2026-09-01T09:30:00-04:00",
            "next_close": "2026-09-01T16:00:00-04:00",
            "market_status": "CLOSED",
        }

    monkeypatch.setattr(broker, "get_clock", mock_get_clock)

    async with async_session_factory() as session:
        orchestrator = VoltronOrchestrator(
            broker_gateway=broker,
            quant_gateway=quant,
            session=session,
        )

        packet = await orchestrator.execute_mandate(
            mandate="Autonomous mandate during closed market",
            symbol="SPY",
            autonomy_level="GUARDED_AUTONOMOUS",
        )

        assert packet.riskCompilerResult.isApproved is True
        # Must be held in AWAITING_APPROVAL because market is closed
        assert packet.status == "AWAITING_APPROVAL"

