from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.infrastructure.database.models import OrderModel, FillModel

class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_order(self, order: OrderModel) -> OrderModel:
        self.session.add(order)
        return order

    async def get_order_by_id(self, order_id: str) -> Optional[OrderModel]:
        stmt = select(OrderModel).where(OrderModel.id == order_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_order_by_client_id(self, client_order_id: str) -> Optional[OrderModel]:
        stmt = select(OrderModel).where(OrderModel.client_order_id == client_order_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_decision(self, decision_id: str) -> List[OrderModel]:
        stmt = select(OrderModel).where(OrderModel.decision_id == decision_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def save_fill(self, fill: FillModel) -> FillModel:
        self.session.add(fill)
        return fill
