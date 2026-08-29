from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.infrastructure.database.models import StrategyCandidateModel

class StrategyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_candidates(self, candidates: List[StrategyCandidateModel]) -> None:
        self.session.add_all(candidates)

    async def get_by_decision(self, decision_id: str) -> List[StrategyCandidateModel]:
        stmt = select(StrategyCandidateModel).where(StrategyCandidateModel.decision_id == decision_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
