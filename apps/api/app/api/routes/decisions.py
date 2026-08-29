from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_db_session
from app.api.deps import get_broker_gateway, get_quant_gateway
from app.services.decision_service import DecisionService
from app.services.execution_service import ExecutionService
from app.domain.models import DecisionPacket, OrderResult

router = APIRouter(prefix="/decisions", tags=["Decisions"])

@router.get("/{decision_id}", response_model=DecisionPacket)
async def get_decision(
    decision_id: str,
    session: AsyncSession = Depends(get_db_session),
    broker_gw = Depends(get_broker_gateway),
    quant_gw = Depends(get_quant_gateway),
):
    service = DecisionService(session, broker_gw, quant_gw)
    return await service.get_decision(decision_id)

@router.post("/{decision_id}/approve", response_model=OrderResult)
async def approve_decision(
    decision_id: str,
    session: AsyncSession = Depends(get_db_session),
    broker_gw = Depends(get_broker_gateway),
):
    exec_service = ExecutionService(session, broker_gw)
    try:
        return await exec_service.approve_and_execute(decision_id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution Pipeline Error: {str(e)}")

@router.post("/{decision_id}/reject")
async def reject_decision(
    decision_id: str,
    session: AsyncSession = Depends(get_db_session),
    broker_gw = Depends(get_broker_gateway),
):
    exec_service = ExecutionService(session, broker_gw)
    try:
        success = await exec_service.reject_decision(decision_id)
        return {"success": success, "decisionId": decision_id, "status": "REJECTED"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
