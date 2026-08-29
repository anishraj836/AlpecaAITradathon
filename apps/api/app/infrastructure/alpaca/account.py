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
            return []

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.ALPACA_BASE_URL}/v2/positions",
                headers=self.headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            return AlpacaNormalizer.normalize_positions(resp.json())
