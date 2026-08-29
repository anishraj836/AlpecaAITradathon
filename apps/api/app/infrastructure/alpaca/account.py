import httpx
from typing import List, Dict, Any, Optional
from app.config import settings
from app.domain.models import AccountInfo, PositionInfo
from app.infrastructure.alpaca.normalizer import AlpacaNormalizer

class AlpacaAccountService:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.client = client
        self.headers = {
            "APCA-API-KEY-ID": settings.ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": settings.ALPACA_SECRET_KEY,
            "Content-Type": "application/json",
        }

    async def get_account(self) -> AccountInfo:
        if not settings.ALPACA_API_KEY or "DUMMY" in settings.ALPACA_API_KEY:
            # Safe deterministic paper fallback
            return AlpacaNormalizer.normalize_account({}, is_paper=settings.ALPACA_PAPER)

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.ALPACA_BASE_URL}/v2/account",
                headers=self.headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            return AlpacaNormalizer.normalize_account(resp.json(), is_paper=settings.ALPACA_PAPER)

    async def get_positions(self) -> List[PositionInfo]:
        if not settings.ALPACA_API_KEY or "DUMMY" in settings.ALPACA_API_KEY:
            return [
                PositionInfo(symbol="SPY260918P00625000", qty=1.0, side="long", marketValue=110.0, avgEntryPrice=1.08, unrealizedPl=2.00, currentPrice=1.10),
                PositionInfo(symbol="SPY260918P00630000", qty=-1.0, side="short", marketValue=-186.0, avgEntryPrice=1.84, unrealizedPl=-2.00, currentPrice=1.86),
                PositionInfo(symbol="SPY260918C00660000", qty=-1.0, side="short", marketValue=-150.0, avgEntryPrice=1.48, unrealizedPl=-2.00, currentPrice=1.50),
                PositionInfo(symbol="SPY260918C00665000", qty=1.0, side="long", marketValue=88.0, avgEntryPrice=0.86, unrealizedPl=2.00, currentPrice=0.88),
            ]

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.ALPACA_BASE_URL}/v2/positions",
                headers=self.headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            return AlpacaNormalizer.normalize_positions(resp.json())
