import httpx
import logging
from typing import List, Dict, Any, Optional
from app.config import settings
from app.domain.models import AccountInfo, PositionInfo
from app.infrastructure.alpaca.normalizer import AlpacaNormalizer

logger = logging.getLogger("AlpacaAccountService")

class AlpacaAccountService:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.client = client
        self.headers = {
            "APCA-API-KEY-ID": settings.ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": settings.ALPACA_SECRET_KEY,
            "Content-Type": "application/json",
        }
        self._sdk_client = None
        if settings.ALPACA_API_KEY and "DUMMY" not in settings.ALPACA_API_KEY:
            try:
                from alpaca.trading.client import TradingClient
                self._sdk_client = TradingClient(
                    api_key=settings.ALPACA_API_KEY,
                    secret_key=settings.ALPACA_SECRET_KEY,
                    paper=settings.ALPACA_PAPER,
                )
            except Exception as e:
                logger.debug(f"alpaca-py TradingClient init skipped: {e}")

    async def get_account(self) -> AccountInfo:
        if not settings.ALPACA_API_KEY or "DUMMY" in settings.ALPACA_API_KEY:
            # Safe deterministic paper fallback
            return AlpacaNormalizer.normalize_account({}, is_paper=settings.ALPACA_PAPER)

        # 1. Try official alpaca-py SDK
        if self._sdk_client:
            try:
                acc = self._sdk_client.get_account()
                raw_dict = {
                    "account_number": getattr(acc, "account_number", "PAPER-01"),
                    "status": getattr(acc, "status", "ACTIVE"),
                    "currency": getattr(acc, "currency", "USD"),
                    "buying_power": float(getattr(acc, "buying_power", 50000.0)),
                    "cash": float(getattr(acc, "cash", 50000.0)),
                    "portfolio_value": float(getattr(acc, "portfolio_value", 100000.0)),
                    "equity": float(getattr(acc, "equity", 100000.0)),
                }
                return AlpacaNormalizer.normalize_account(raw_dict, is_paper=settings.ALPACA_PAPER)
            except Exception:
                pass

        # 2. HTTPX REST fallback
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

        # 1. Try official alpaca-py SDK
        if self._sdk_client:
            try:
                positions = self._sdk_client.get_all_positions()
                raw_positions = []
                for p in positions:
                    raw_positions.append({
                        "symbol": getattr(p, "symbol", ""),
                        "qty": float(getattr(p, "qty", 0.0)),
                        "side": getattr(p, "side", "long"),
                        "market_value": float(getattr(p, "market_value", 0.0)),
                        "avg_entry_price": float(getattr(p, "avg_entry_price", 0.0)),
                        "unrealized_pl": float(getattr(p, "unrealized_pl", 0.0)),
                        "current_price": float(getattr(p, "current_price", 0.0)),
                    })
                return AlpacaNormalizer.normalize_positions(raw_positions)
            except Exception:
                pass

        # 2. HTTPX REST fallback
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.ALPACA_BASE_URL}/v2/positions",
                headers=self.headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            return AlpacaNormalizer.normalize_positions(resp.json())

    async def close_all_positions(self) -> Dict[str, Any]:
        if not settings.ALPACA_API_KEY or "DUMMY" in settings.ALPACA_API_KEY:
            return {"status": "success", "closed": 0}

        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{settings.ALPACA_BASE_URL}/v2/positions",
                headers=self.headers,
                timeout=10.0,
            )
            return {"status": "success", "response": resp.json() if resp.status_code == 200 else resp.text}
