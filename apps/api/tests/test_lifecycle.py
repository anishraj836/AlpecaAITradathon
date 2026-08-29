import pytest
from app.services.execution_service import ExecutionService
from app.infrastructure.alpaca.mcp_client import AlpacaBrokerGateway
from app.infrastructure.options.mock_gateway import MockOptionsIntelligenceGateway
from app.infrastructure.database.session import async_session_factory
from app.infrastructure.database.repositories.decisions import DecisionRepository
from app.domain.models import DecisionPacket

@pytest.mark.asyncio
async def test_lifecycle_allowed_and_disallowed_transitions():
    broker = AlpacaBrokerGateway()
    quant = MockOptionsIntelligenceGateway()
    strategy = (await quant.generate_candidates("SPY"))[0]
    risk_approved = await quant.compile_risk(strategy, 1000000.0)

    # 1. Create Decision in AWAITING_APPROVAL
    packet = DecisionPacket(
        id="DEC-LIFE-01",
        createdAt="2026-08-29T10:00:00Z",
        underlying="SPY",
        spotPrice=645.31,
        marketRegime="Range-Bound",
        iv30=18.4,
        ivRank=72.1,
        aiConfidence=0.81,
        strategy=strategy,
        evidence={"description": "Test", "putSkewElevated": True, "termStructureRich": True},
        whyThisTrade=["Test"],
        criticAnalysis={"primaryFailureMode": "None", "details": "Test"},
        riskCompilerResult=risk_approved,
        status="AWAITING_APPROVAL",
    )

    async with async_session_factory() as session:
        dec_repo = DecisionRepository(session)
        await dec_repo.save(packet)
        await session.commit()

    # 2. Approve Decision -> Moves to APPROVED
    async with async_session_factory() as session:
        exec_service = ExecutionService(session, broker)
        order = await exec_service.approve_and_execute(packet.id)
        assert order.status in ["accepted", "filled"]

    # 3. Disallowed Transition: Reject an already APPROVED decision
    async with async_session_factory() as session:
        exec_service = ExecutionService(session, broker)
        with pytest.raises(ValueError, match="already 'APPROVED' and cannot be rejected"):
            await exec_service.reject_decision(packet.id)

@pytest.mark.asyncio
async def test_lifecycle_rejected_cannot_be_approved():
    broker = AlpacaBrokerGateway()
    quant = MockOptionsIntelligenceGateway()
    strategy = (await quant.generate_candidates("SPY"))[0]
    risk_approved = await quant.compile_risk(strategy, 1000000.0)

    packet = DecisionPacket(
        id="DEC-LIFE-REJ-01",
        createdAt="2026-08-29T10:00:00Z",
        underlying="SPY",
        spotPrice=645.31,
        marketRegime="Range-Bound",
        iv30=18.4,
        ivRank=72.1,
        aiConfidence=0.81,
        strategy=strategy,
        evidence={"description": "Test", "putSkewElevated": True, "termStructureRich": True},
        whyThisTrade=["Test"],
        criticAnalysis={"primaryFailureMode": "None", "details": "Test"},
        riskCompilerResult=risk_approved,
        status="AWAITING_APPROVAL",
    )

    async with async_session_factory() as session:
        dec_repo = DecisionRepository(session)
        await dec_repo.save(packet)
        await session.commit()

    # Reject the decision
    async with async_session_factory() as session:
        exec_service = ExecutionService(session, broker)
        await exec_service.reject_decision(packet.id)

    # Disallowed: Try to approve a REJECTED decision
    async with async_session_factory() as session:
        exec_service = ExecutionService(session, broker)
        with pytest.raises(ValueError, match="terminal status 'REJECTED'"):
            await exec_service.approve_and_execute(packet.id)
