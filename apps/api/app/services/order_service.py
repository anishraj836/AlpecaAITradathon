from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.alpaca.gateway import BrokerGateway
from app.infrastructure.database.repositories.orders import OrderRepository
from app.infrastructure.database.models import OrderModel
from app.domain.models import OrderResult, DecisionPacket

class OrderService:
    def __init__(self, session: AsyncSession, broker_gateway: BrokerGateway):
        self.session = session
        self.repo = OrderRepository(session)
        self.broker_gateway = broker_gateway

    async def execute_paper_order(self, decision: DecisionPacket) -> OrderResult:
        result = await self.broker_gateway.place_multileg_order(decision)
        
        # Persist to database ledger
        order_model = OrderModel(
            id=result.orderId,
            decision_id=decision.id,
            client_order_id=result.clientOrderId,
            broker_order_id=result.orderId,
            symbol=decision.underlying,
            order_type="limit",
            status=result.status,
            avg_price=result.avgPrice,
            qty=result.qty,
            raw_payload=result.rawResponse,
        )
        await self.repo.save_order(order_model)
        return result

    async def get_order_status(self, order_id: str) -> OrderResult:
        return await self.broker_gateway.get_order(order_id)
