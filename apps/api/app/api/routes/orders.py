from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_db_session
from app.api.deps import get_broker_gateway
from app.services.execution_service import ExecutionService
from app.domain.models import OrderResult

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("/{order_id}", response_model=OrderResult)
async def get_order_status(
    order_id: str,
    session: AsyncSession = Depends(get_db_session),
    broker_gw = Depends(get_broker_gateway),
):
    service = ExecutionService(session, broker_gw)
    try:
        return await service.get_order_status(order_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found: {str(e)}")
