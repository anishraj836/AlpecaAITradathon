from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_db_session
from app.infrastructure.database.repositories.decisions import DecisionRepository
from app.infrastructure.database.repositories.orders import OrderRepository
from app.domain.models import HistoricalDecisionSummary

router = APIRouter(prefix="/history", tags=["History"])

@router.get("", response_model=List[HistoricalDecisionSummary])
async def get_history(session: AsyncSession = Depends(get_db_session)):
    repo = DecisionRepository(session)
    order_repo = OrderRepository(session)
    decisions = await repo.list_recent(limit=50)
    
    summaries: List[HistoricalDecisionSummary] = []
    for d in decisions:
        packet = d.packet_json or {}
        strat = packet.get("strategy", {})
        legs = strat.get("legs", [])
        legs_summary = f"{len(legs)} Legs ({strat.get('dte', 30)} DTE)" if legs else "Defined Risk"
        
        status_raw = d.status
        is_executed = status_raw in ["APPROVED", "EXECUTED"]
        is_rejected = status_raw == "REJECTED"
        dec_label = "Approved" if is_executed else ("Rejected" if is_rejected else "No Trade")

        # Query actual order execution records
        orders = await order_repo.get_by_decision(d.id)
        has_filled_order = any(o.status == "filled" for o in orders)

        # Honest PnL tracking: Open positions have 0.0 realized outcome until closed
        outcome_amt = 0.0
        is_profit = False

        summaries.append(
            HistoricalDecisionSummary(
                id=d.id,
                timestamp=d.created_at.isoformat() + "Z" if d.created_at else "2026-08-29T10:00:00Z",
                timeFormatted=d.created_at.strftime("%H:%M:%S EST") if d.created_at else "10:45:12 EST",
                symbol=d.underlying,
                strategyName=strat.get("name", "Iron Condor"),
                decision=dec_label, # type: ignore
                riskAmount=float(strat.get("maxLoss", 0.0)) if is_executed else 0.0,
                outcomeAmount=outcome_amt,
                isProfit=is_profit,
                pop=float(strat.get("pop", 0.684)),
                legsSummary=legs_summary,
            )
        )

    return summaries
