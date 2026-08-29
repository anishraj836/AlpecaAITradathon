import pytest
import asyncio
from app.services.event_broadcaster import broadcaster
from app.domain.models import OrchestratorEvent

@pytest.mark.asyncio
async def test_sse_broadcaster_event_stream():
    events_received = []

    async def consumer():
        async for sse_chunk in broadcaster.subscribe("DEC-SSE-TEST"):
            events_received.append(sse_chunk)
            if len(events_received) >= 2:
                break

    consumer_task = asyncio.create_task(consumer())
    await asyncio.sleep(0.05)  # Allow subscriber to connect

    event_1 = OrchestratorEvent(
        decisionId="DEC-SSE-TEST",
        eventType="analysis_created",
        stage="INIT",
        status="ACTIVE",
        message="Mandate initialized",
        timestamp="2026-08-29T10:00:00Z",
    )
    event_2 = OrchestratorEvent(
        decisionId="DEC-SSE-TEST",
        eventType="decision_completed",
        stage="COMPLETE",
        status="COMPLETE",
        message="Decision complete",
        timestamp="2026-08-29T10:00:01Z",
    )

    await broadcaster.broadcast(event_1)
    await broadcaster.broadcast(event_2)

    await asyncio.wait_for(consumer_task, timeout=2.0)
    assert len(events_received) == 2
    assert "analysis_created" in events_received[0]
    assert "decision_completed" in events_received[1]
