from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from app.services.event_broadcaster import broadcaster

router = APIRouter(tags=["Events & SSE"])

@router.get("/stream/orchestrator")
async def stream_orchestrator(decision_id: Optional[str] = Query(None, description="Optional decision ID filter")):
    """
    Real-time Server-Sent Events (SSE) stream delivering live agent execution events and telemetry tokens.
    Supports reconnection and historical event catch-up.
    """
    return StreamingResponse(
        broadcaster.subscribe(decision_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
