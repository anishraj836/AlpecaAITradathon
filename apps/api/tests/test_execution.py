import pytest
from app.services.execution_service import MlegOrderCompiler, ExecutionService
from app.infrastructure.alpaca.mcp_client import AlpacaBrokerGateway
from app.infrastructure.options.mock_gateway import MockOptionsIntelligenceGateway
from app.infrastructure.database.session import async_session_factory
from app.infrastructure.database.repositories.decisions import DecisionRepository
from app.domain.models import DecisionPacket, StrategyCandidate, OptionLeg

@pytest.mark.asyncio
async def test_mleg_compiler_valid_condor():
    quant = MockOptionsIntelligenceGateway()
    strategy = (await quant.generate_candidates("SPY"))[0]
    
    packet = DecisionPacket(
        id="DEC-COMP-01",
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
        riskCompilerResult=await quant.compile_risk(strategy, 1000000.0),
        status="AWAITING_APPROVAL",
    )

    payload = MlegOrderCompiler.compile_and_validate(packet, target_qty=1)
    assert payload.symbol == "SPY"
    assert payload.orderType == "limit"
    assert payload.timeInForce == "day"
    assert payload.limitPrice == abs(strategy.netCreditOrDebit)
    assert len(payload.legs) == 4
    assert payload.legs[0].position_intent == "buy_to_open"
    assert payload.legs[1].position_intent == "sell_to_open"

@pytest.mark.asyncio
async def test_mleg_compiler_mismatched_underlying_fails():
    quant = MockOptionsIntelligenceGateway()
    strategy = (await quant.generate_candidates("SPY"))[0]
    strategy.underlying = "QQQ"  # Mismatch

    packet = DecisionPacket(
        id="DEC-FAIL-01",
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
        riskCompilerResult=await quant.compile_risk(strategy, 1000000.0),
        status="AWAITING_APPROVAL",
    )

    with pytest.raises(ValueError, match="underlying 'QQQ' does not match"):
        MlegOrderCompiler.compile_and_validate(packet)

@pytest.mark.asyncio
async def test_execution_service_approve_and_idempotency():
    broker = AlpacaBrokerGateway()
    quant = MockOptionsIntelligenceGateway()
    strategy = (await quant.generate_candidates("SPY"))[0]

    packet = DecisionPacket(
        id="DEC-EXEC-IDEMP-01",
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
        riskCompilerResult=await quant.compile_risk(strategy, 1000000.0),
        status="AWAITING_APPROVAL",
    )

    # 1. Save Decision to DB
    async with async_session_factory() as session:
        dec_repo = DecisionRepository(session)
        await dec_repo.save(packet)
        await session.commit()

    # 2. First Approval -> Dispatches order and updates to APPROVED
    async with async_session_factory() as session:
        exec_service = ExecutionService(session, broker)
        order_1 = await exec_service.approve_and_execute(packet.id)
        assert order_1.decisionId == packet.id
        assert order_1.status in ["accepted", "filled"]
        assert order_1.broker == "ALPACA_PAPER"

    # 3. Second Approval -> Idempotent check (returns existing order without error or duplicate dispatch)
    async with async_session_factory() as session:
        exec_service = ExecutionService(session, broker)
        order_2 = await exec_service.approve_and_execute(packet.id)
        assert order_2.orderId == order_1.orderId
        assert order_2.clientOrderId == order_1.clientOrderId

@pytest.mark.asyncio
async def test_execution_service_risk_failure_rejection():
    broker = AlpacaBrokerGateway()
    quant = MockOptionsIntelligenceGateway()
    strategy = (await quant.generate_candidates("SPY"))[0]

    # Create unapproved risk check
    risk_failed = await quant.compile_risk(strategy, 1000000.0)
    risk_failed.isApproved = False

    packet = DecisionPacket(
        id="DEC-EXEC-RISK-FAIL",
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
        riskCompilerResult=risk_failed,
        status="AWAITING_APPROVAL",
    )

    async with async_session_factory() as session:
        dec_repo = DecisionRepository(session)
        await dec_repo.save(packet)
        await session.commit()

    async with async_session_factory() as session:
        exec_service = ExecutionService(session, broker)
        with pytest.raises(ValueError, match="Deterministic Risk Compiler Violation"):
            await exec_service.approve_and_execute(packet.id)

@pytest.mark.asyncio
async def test_execution_service_reject():
    broker = AlpacaBrokerGateway()
    quant = MockOptionsIntelligenceGateway()
    strategy = (await quant.generate_candidates("SPY"))[0]

    packet = DecisionPacket(
        id="DEC-EXEC-REJECT-01",
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
        riskCompilerResult=await quant.compile_risk(strategy, 1000000.0),
        status="AWAITING_APPROVAL",
    )

    async with async_session_factory() as session:
        dec_repo = DecisionRepository(session)
        await dec_repo.save(packet)
        await session.commit()

    async with async_session_factory() as session:
        exec_service = ExecutionService(session, broker)
        rejected = await exec_service.reject_decision(packet.id)
        assert rejected is True

    async with async_session_factory() as session:
        dec_repo = DecisionRepository(session)
        updated = await dec_repo.get_by_id(packet.id)
        assert updated.status == "REJECTED"
