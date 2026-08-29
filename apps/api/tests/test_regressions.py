import pytest
import asyncio
import httpx
from app.main import app
from app.services.execution_service import ExecutionService
from app.services.event_broadcaster import broadcaster
from app.infrastructure.alpaca.mcp_client import AlpacaBrokerGateway
from app.infrastructure.options.mock_gateway import MockOptionsIntelligenceGateway
from app.infrastructure.database.session import async_session_factory
from app.infrastructure.database.repositories.decisions import DecisionRepository
from app.infrastructure.database.repositories.agents import AgentRepository
from app.infrastructure.database.models import AgentRunModel
from app.domain.models import DecisionPacket, OrchestratorEvent

@pytest.mark.asyncio
async def test_concurrent_approval_race_condition():
    broker = AlpacaBrokerGateway()
    quant = MockOptionsIntelligenceGateway()
    strategy = (await quant.generate_candidates("SPY"))[0]
    risk_approved = await quant.compile_risk(strategy, 1000000.0)

    packet = DecisionPacket(
        id="DEC-CONCURRENT-RACE-01",
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

    # Save to DB
    async with async_session_factory() as session:
        dec_repo = DecisionRepository(session)
        await dec_repo.save(packet)
        await session.commit()

    # Launch 5 concurrent approval requests
    async def approve_task():
        async with async_session_factory() as session:
            exec_service = ExecutionService(session, broker)
            return await exec_service.approve_and_execute(packet.id)

    results = await asyncio.gather(*[approve_task() for _ in range(5)])

    # Verify all 5 concurrent calls returned the exact same Order ID
    order_ids = [r.orderId for r in results]
    assert len(set(order_ids)) == 1, f"Expected 1 unique order ID, got: {order_ids}"
    assert results[0].status in ["accepted", "filled"]

@pytest.mark.asyncio
async def test_replay_route_persisted_decision():
    # Save a decision with agent runs
    decision_id = "DEC-REPLAY-TEST-01"
    packet = DecisionPacket(
        id=decision_id,
        createdAt="2026-08-29T10:00:00Z",
        underlying="SPY",
        spotPrice=645.31,
        marketRegime="Range-Bound",
        iv30=18.4,
        ivRank=72.1,
        aiConfidence=0.85,
        strategy=(await MockOptionsIntelligenceGateway().generate_candidates("SPY"))[0],
        evidence={"description": "Test", "putSkewElevated": True, "termStructureRich": True},
        whyThisTrade=["Test"],
        criticAnalysis={"primaryFailureMode": "None", "details": "Test"},
        riskCompilerResult=await MockOptionsIntelligenceGateway().compile_risk(
            (await MockOptionsIntelligenceGateway().generate_candidates("SPY"))[0], 1000000.0
        ),
        status="APPROVED",
    )

    async with async_session_factory() as session:
        dec_repo = DecisionRepository(session)
        agent_repo = AgentRepository(session)
        await dec_repo.save(packet)
        await agent_repo.save_agent_runs([
            AgentRunModel(
                id=f"{decision_id}-run1",
                decision_id=decision_id,
                agent_role="RESEARCHER",
                title="Market Regime Identified",
                status="COMPLETE",
                summary="Range-bound identified",
            ),
            AgentRunModel(
                id=f"{decision_id}-run2",
                decision_id=decision_id,
                agent_role="VOLATILITY_ANALYST",
                title="Put Skew Detected",
                status="COMPLETE",
                summary="Elevated put skew",
            )
        ])
        await session.commit()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/replay/{decision_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["replayId"] == decision_id
        assert data["symbol"] == "SPY"
        assert len(data["events"]) >= 4
        assert any(e["stage"] == "RESEARCHER" for e in data["events"])
        assert any(e["stage"] == "VOLATILITY_ANALYST" for e in data["events"])

@pytest.mark.asyncio
async def test_sse_broadcaster_filtered_subscriptions():
    dec_a_events = []
    dec_b_events = []

    async def consume_a():
        async for chunk in broadcaster.subscribe("DEC-FILTER-A"):
            dec_a_events.append(chunk)
            if len(dec_a_events) >= 1:
                break

    async def consume_b():
        async for chunk in broadcaster.subscribe("DEC-FILTER-B"):
            dec_b_events.append(chunk)
            if len(dec_b_events) >= 1:
                break

    task_a = asyncio.create_task(consume_a())
    task_b = asyncio.create_task(consume_b())
    await asyncio.sleep(0.05)

    # Broadcast event for A
    await broadcaster.broadcast(OrchestratorEvent(
        decisionId="DEC-FILTER-A",
        eventType="analysis_created",
        stage="INIT",
        status="ACTIVE",
        message="A event",
        timestamp="2026-08-29T10:00:00Z",
    ))

    # Broadcast event for B
    await broadcaster.broadcast(OrchestratorEvent(
        decisionId="DEC-FILTER-B",
        eventType="analysis_created",
        stage="INIT",
        status="ACTIVE",
        message="B event",
        timestamp="2026-08-29T10:00:00Z",
    ))

    await asyncio.wait_for(asyncio.gather(task_a, task_b), timeout=2.0)
    assert len(dec_a_events) == 1
    assert "DEC-FILTER-A" in dec_a_events[0]
    assert len(dec_b_events) == 1
    assert "DEC-FILTER-B" in dec_b_events[0]

@pytest.mark.asyncio
async def test_get_decision_not_found_returns_404_and_does_not_mutate_db():
    non_existent_id = "DEC-NON-EXISTENT-XYZ-999"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/decisions/{non_existent_id}")
        assert resp.status_code == 404

    # Verify DB was NOT mutated
    async with async_session_factory() as session:
        dec_repo = DecisionRepository(session)
        assert await dec_repo.get_by_id(non_existent_id) is None

@pytest.mark.asyncio
async def test_get_order_dynamic_decision_id():
    broker = AlpacaBrokerGateway()
    order = await broker.get_order("ALP-ORD-TEST-12345")
    assert order.decisionId == "DEC-TEST-12345"
    assert order.status == "filled"

@pytest.mark.asyncio
async def test_counterfactual_post_route_params():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Test without body
        resp_empty = await client.post("/api/quant/counterfactual", json={})
        assert resp_empty.status_code == 200
        data_empty = resp_empty.json()
        assert "baseline" in data_empty
        assert "scenario" in data_empty

        # Test with custom params
        resp_custom = await client.post(
            "/api/quant/counterfactual",
            json={"targetDelta": 18.0, "dteDays": 60, "budget": 5000.0},
        )
        assert resp_custom.status_code == 200
        data_custom = resp_custom.json()
        assert data_custom["scenario"]["targetDelta"] == 18.0
        assert data_custom["scenario"]["dteDays"] == 60
        assert data_custom["scenario"]["allocatedBudget"] == 5000.0
