from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.infrastructure.database.models import AgentRunModel

class AgentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_agent_runs(self, runs: List[AgentRunModel]) -> None:
        self.session.add_all(runs)

    async def get_by_decision(self, decision_id: str) -> List[AgentRunModel]:
        stmt = select(AgentRunModel).where(AgentRunModel.decision_id == decision_id).order_by(AgentRunModel.created_at.asc())
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
