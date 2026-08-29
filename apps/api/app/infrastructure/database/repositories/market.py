from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.infrastructure.database.models import MarketSnapshotModel, OptionSnapshotModel

class MarketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_market_snapshot(self, snapshot: MarketSnapshotModel) -> MarketSnapshotModel:
        self.session.add(snapshot)
        return snapshot

    async def get_latest_market_snapshot(self, symbol: str) -> Optional[MarketSnapshotModel]:
        stmt = select(MarketSnapshotModel).where(MarketSnapshotModel.symbol == symbol).order_by(MarketSnapshotModel.created_at.desc()).limit(1)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def save_option_snapshots(self, snapshots: List[OptionSnapshotModel]) -> None:
        self.session.add_all(snapshots)

    async def get_option_chain_snapshots(self, underlying: str) -> List[OptionSnapshotModel]:
        stmt = select(OptionSnapshotModel).where(OptionSnapshotModel.underlying == underlying).order_by(OptionSnapshotModel.strike.asc())
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
