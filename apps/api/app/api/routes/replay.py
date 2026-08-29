from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_db_session
from app.infrastructure.database.repositories.decisions import DecisionRepository
from app.infrastructure.database.repositories.agents import AgentRepository
from app.infrastructure.database.repositories.orders import OrderRepository

router = APIRouter(prefix="/replay", tags=["Replay"])

@router.get("/{replay_id}")
async def get_replay_session(
    replay_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    dec_repo = DecisionRepository(session)
    agent_repo = AgentRepository(session)
    order_repo = OrderRepository(session)

    db_dec = await dec_repo.get_by_id(replay_id)
    if db_dec:
        packet = db_dec.packet_json or {}
        strat = packet.get("strategy", {})
        runs = await agent_repo.get_by_decision(replay_id)
        
        events: List[Dict[str, Any]] = [
            {
                "timeSec": 0,
                "stage": "INIT",
                "title": f"Mandate Initialized for {db_dec.underlying}",
                "spotPrice": db_dec.spot_price,
            },
            {
                "timeSec": 2,
                "stage": "DATA_FETCH",
                "title": f"Market Snapshot Loaded (${db_dec.spot_price:.2f})",
                "iv30": db_dec.iv30,
            }
        ]

        time_cursor = 4
        for r in runs:
            events.append({
                "timeSec": time_cursor,
                "stage": r.agent_role,
                "title": r.title,
                "status": r.status,
                "summary": r.summary,
            })
            time_cursor += 3

        # Check if order was executed
        client_order_id = f"cl-{replay_id}"
        order = await order_repo.get_order_by_client_id(client_order_id)
        if order:
            events.append({
                "timeSec": time_cursor,
                "stage": "EXECUTION",
                "title": f"Alpaca Paper Executed ({order.status.upper()})",
                "orderId": order.id,
                "fillPrice": order.avg_price,
            })
            time_cursor += 2

        return {
            "replayId": replay_id,
            "symbol": db_dec.underlying,
            "strategy": strat.get("name", "Iron Condor"),
            "status": db_dec.status,
            "durationSec": time_cursor,
            "events": events,
        }

    # Fallback to demo session if replay_id not found in DB
    return {
        "replayId": replay_id,
        "symbol": "SPY",
        "strategy": "Iron Condor",
        "durationSec": 13,
        "events": [
            {"timeSec": 0, "stage": "CONTEXT", "title": "Market Context Loaded", "vix": 14.25},
            {"timeSec": 6, "stage": "GENERATION", "title": "Iron Condor Structured", "score": 86.2},
            {"timeSec": 13, "stage": "EXECUTION", "title": "Alpaca Paper Executed", "fillPrice": 1.45},
        ]
    }
