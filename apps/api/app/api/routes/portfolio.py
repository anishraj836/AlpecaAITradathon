from fastapi import APIRouter, Depends
from app.api.deps import get_broker_gateway
from app.infrastructure.alpaca.gateway import BrokerGateway
from app.domain.models import PortfolioSummary

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

@router.get("", response_model=PortfolioSummary)
async def get_portfolio_summary(broker_gw: BrokerGateway = Depends(get_broker_gateway)):
    account = await broker_gw.get_account()
    positions = await broker_gw.get_positions()
    
    total_unrealized = sum(p.unrealizedPl for p in positions)
    
    return PortfolioSummary(
        account=account,
        positions=positions,
        netDelta=0.12,
        netTheta=48.50,
        netVega=-12.40,
        netGamma=0.008,
        unrealizedPnl=total_unrealized if positions else 84.00,
        realizedTodayPnl=138.00,
        profitTargetPct=50.0,
        stopLossMultiplier=2.0,
    )
