import pytest
from app.infrastructure.database.session import async_session_factory
from app.infrastructure.database.repositories.decisions import DecisionRepository
from app.infrastructure.database.repositories.orders import OrderRepository
from app.infrastructure.database.models import OrderModel
from app.infrastructure.options.mock_gateway import MockOptionsIntelligenceGateway
from app.domain.models import DecisionPacket

@pytest.mark.asyncio
async def test_decision_repository_save_and_get():
    quant = MockOptionsIntelligenceGateway()
    strategy = (await quant.generate_candidates("SPY"))[0]

    packet = DecisionPacket(
        id="DEC-DB-TEST-01",
        createdAt="2026-08-29T10:00:00Z",
        underlying="SPY",
        spotPrice=645.31,
        marketRegime="Range-Bound",
        iv30=18.4,
        ivRank=72.1,
        aiConfidence=0.81,
        strategy=strategy,
        evidence={"description": "DB test", "putSkewElevated": True, "termStructureRich": True},
        whyThisTrade=["DB test"],
        criticAnalysis={"primaryFailureMode": "None", "details": "DB test"},
        riskCompilerResult=await quant.compile_risk(strategy, 1000000.0),
        status="AWAITING_APPROVAL",
    )

    async with async_session_factory() as session:
        repo = DecisionRepository(session)
        saved = await repo.save(packet)
        await session.commit()
        assert saved.id == "DEC-DB-TEST-01"

    async with async_session_factory() as session:
        repo = DecisionRepository(session)
        retrieved = await repo.get_by_id("DEC-DB-TEST-01")
        assert retrieved is not None
        assert retrieved.underlying == "SPY"
        assert retrieved.status == "AWAITING_APPROVAL"

@pytest.mark.asyncio
async def test_order_repository_save_and_get():
    order = OrderModel(
        id="ORD-TEST-99",
        decision_id="DEC-DB-TEST-01",
        client_order_id="cl-DEC-DB-TEST-01",
        broker_order_id="ALP-ORD-99",
        symbol="SPY",
        order_type="limit",
        status="accepted",
        avg_price=1.38,
        qty=1,
    )

    async with async_session_factory() as session:
        repo = OrderRepository(session)
        await repo.save_order(order)
        await session.commit()

    async with async_session_factory() as session:
        repo = OrderRepository(session)
        retrieved = await repo.get_order_by_id("ORD-TEST-99")
        assert retrieved is not None
        assert retrieved.client_order_id == "cl-DEC-DB-TEST-01"
        assert retrieved.avg_price == 1.38
