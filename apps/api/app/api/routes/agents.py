from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
import asyncio
import json

from app.domain.models import (
    AgentsDashboardResponse,
    AgentLogEntry,
    AutonomousDaemonState,
    AutonomousControlRequest,
)
from app.services.autonomous_service import autonomous_agent_service
from app.services.event_broadcaster import broadcaster

router = APIRouter(prefix="/agents", tags=["Autonomous Agents Fleet"])

@router.get("/status", response_model=AgentsDashboardResponse)
async def get_agents_status():
    """Retrieve full dashboard telemetry for the live fleet of autonomous agents and the background worker daemon."""
    return autonomous_agent_service.get_dashboard_state()

@router.get("/logs", response_model=List[AgentLogEntry])
async def get_agent_logs(
    role: Optional[str] = Query(None, description="Filter logs by agent role"),
    level: Optional[str] = Query(None, description="Filter logs by severity level"),
    limit: int = Query(100, ge=1, le=500),
):
    """Retrieve recent chronological agent execution logs."""
    return autonomous_agent_service.get_logs(role=role, level=level, limit=limit)

@router.post("/control", response_model=AutonomousDaemonState)
async def control_autonomous_daemon(req: AutonomousControlRequest):
    """Control the autonomous worker loop (PAUSE, RESUME, TRIGGER_SCAN, SET_AUTONOMY, SET_WATCHLIST)."""
    return await autonomous_agent_service.control(req)

@router.get("/stream")
async def stream_agents_telemetry():
    """Real-time Server-Sent Events (SSE) stream of agent heartbeat telemetry and live logs."""
    async def event_generator():
        # Yield initial state
        initial_state = autonomous_agent_service.get_dashboard_state()
        yield f"event: initial_state\ndata: {json.dumps(initial_state.model_dump())}\n\n"

        while True:
            await asyncio.sleep(2.0)
            state = autonomous_agent_service.get_dashboard_state()
            yield f"event: agent_heartbeat\ndata: {json.dumps(state.model_dump())}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
