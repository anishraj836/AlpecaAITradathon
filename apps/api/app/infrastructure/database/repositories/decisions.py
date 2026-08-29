from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List
from app.infrastructure.database.models import DecisionModel
from app.domain.models import DecisionPacket

class DecisionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, packet: DecisionPacket) -> DecisionModel:
        existing = await self.get_by_id(packet.id)
        if existing:
            existing.status = packet.status
            existing.ai_confidence = packet.aiConfidence
            existing.spot_price = packet.spotPrice
            existing.packet_json = packet.model_dump()
            return existing
        else:
            model = DecisionModel(
                id=packet.id,
                underlying=packet.underlying,
                spot_price=packet.spotPrice,
                market_regime=packet.marketRegime,
                iv30=packet.iv30,
                iv_rank=packet.ivRank,
                ai_confidence=packet.aiConfidence,
                status=packet.status,
                packet_json=packet.model_dump(),
            )
            self.session.add(model)
            return model

    async def get_by_id(self, decision_id: str) -> Optional[DecisionModel]:
        stmt = select(DecisionModel).where(DecisionModel.id == decision_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_recent(self, limit: int = 20) -> List[DecisionModel]:
        stmt = select(DecisionModel).order_by(DecisionModel.created_at.desc()).limit(limit)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def update_status(self, decision_id: str, new_status: str) -> bool:
        stmt = update(DecisionModel).where(DecisionModel.id == decision_id).values(status=new_status)
        res = await self.session.execute(stmt)
        return res.rowcount > 0
