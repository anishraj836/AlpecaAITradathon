from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.infrastructure.database.models import RiskCheckModel

class RiskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, check: RiskCheckModel) -> RiskCheckModel:
        self.session.add(check)
        return check

    async def get_by_decision(self, decision_id: str) -> Optional[RiskCheckModel]:
        stmt = select(RiskCheckModel).where(RiskCheckModel.decision_id == decision_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
