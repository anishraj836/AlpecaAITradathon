import httpx
from typing import Optional, Dict, Any
from app.config import settings
from app.domain.models import MarketContext
from app.infrastructure.alpaca.normalizer import AlpacaNormalizer

class AlpacaMarketDataService:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.client = client
        self.headers = {
            "APCA-API-KEY-ID": settings.ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": settings.ALPACA_SECRET_KEY,
            "Content-Type": "application/json",
        }

    async def get_market_context(self, symbol: str) -> MarketContext:
        symbol = symbol.upper()
        if not settings.ALPACA_API_KEY or "DUMMY" in settings.ALPACA_API_KEY:
            # Deterministic live benchmark fallback
            return AlpacaNormalizer.normalize_market_context(
                symbol=symbol,
                price=645.31 if symbol == "SPY" else 500.25,
                change_pct=0.82 if symbol == "SPY" else 0.45,
                high=647.20,
                low=642.10,
                volume=82500000,
            )

        async with httpx.AsyncClient() as client:
            # Fetch latest trade / snapshot
            resp = await client.get(
                f"{settings.ALPACA_DATA_URL}/v2/stocks/{symbol}/snapshot",
                headers=self.headers,
                timeout=10.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                latest_trade = data.get("latestTrade", {})
                daily_bar = data.get("dailyBar", {})
                prev_daily_bar = data.get("prevDailyBar", {})

                price = float(latest_trade.get("p", daily_bar.get("c", 645.31)))
                prev_close = float(prev_daily_bar.get("c", price))
                change_pct = ((price - prev_close) / prev_close * 100.0) if prev_close else 0.0

                return AlpacaNormalizer.normalize_market_context(
                    symbol=symbol,
                    price=price,
                    change_pct=change_pct,
                    high=float(daily_bar.get("h", price * 1.01)),
                    low=float(daily_bar.get("l", price * 0.99)),
                    volume=int(daily_bar.get("v", 80000000)),
                )
            else:
                return AlpacaNormalizer.normalize_market_context(symbol=symbol, price=645.31, change_pct=0.82)

    async def get_clock(self) -> Dict[str, Any]:
        """
        Query Alpaca's live clock API to determine if market is OPEN, PRE_MARKET, or CLOSED.
        """
        if not settings.ALPACA_API_KEY or "DUMMY" in settings.ALPACA_API_KEY:
            # Deterministic test mode: open by default
            return {
                "is_open": True,
                "next_open": "2026-09-01T09:30:00-04:00",
                "next_close": "2026-09-01T16:00:00-04:00",
                "market_status": "OPEN",
            }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.ALPACA_BASE_URL}/v2/clock",
                    headers=self.headers,
                    timeout=5.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    is_open = bool(data.get("is_open", False))
                    return {
                        "is_open": is_open,
                        "next_open": str(data.get("next_open", "")),
                        "next_close": str(data.get("next_close", "")),
                        "market_status": "OPEN" if is_open else "CLOSED",
                        "timestamp": str(data.get("timestamp", "")),
                    }
        except Exception:
            pass

        # Fallback to local US/Eastern timezone calculation
        from datetime import datetime, timezone
        try:
            import zoneinfo
            eastern = zoneinfo.ZoneInfo("America/New_York")
        except Exception:
            eastern = timezone.utc

        now_est = datetime.now(eastern)
        is_weekday = now_est.weekday() < 5
        is_market_hours = (
            (now_est.hour > 9 or (now_est.hour == 9 and now_est.minute >= 30))
            and now_est.hour < 16
        )
        is_open = is_weekday and is_market_hours
        return {
            "is_open": is_open,
            "next_open": "09:30:00 EST",
            "next_close": "16:00:00 EST",
            "market_status": "OPEN" if is_open else "CLOSED",
        }

    async def get_news(self, symbol: str, limit: int = 5) -> list:
        """
        Fetch real-time market news headlines and summaries from Alpaca News API (GET /v2/news).
        """
        symbol = symbol.upper()
        if not settings.ALPACA_API_KEY or "DUMMY" in settings.ALPACA_API_KEY:
            # Deterministic news fixture for testing and offline modes
            return [
                {
                    "headline": f"{symbol} consolidates in low-dispersion corridor as options skew reflects tail protection",
                    "summary": f"Options trading volume on {symbol} reflects steady institutional hedging with elevated downside put demand.",
                    "source": "MarketWatch Wire",
                    "symbols": [symbol],
                    "created_at": "2026-08-31T12:30:00Z",
                },
                {
                    "headline": f"Macro volatility indices contract as equity markets absorb economic growth metrics",
                    "summary": "Large cap ETF implied volatility remains compressed across 30-day front-month expiries.",
                    "source": "Alpaca Financial Feed",
                    "symbols": [symbol],
                    "created_at": "2026-08-31T11:00:00Z",
                },
            ]

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.ALPACA_DATA_URL}/v2/news",
                    headers=self.headers,
                    params={"symbols": symbol, "limit": limit, "include_content": "false"},
                    timeout=8.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    raw_news = data.get("news", [])
                    return [
                        {
                            "headline": item.get("headline", ""),
                            "summary": item.get("summary", ""),
                            "source": item.get("source", "Alpaca"),
                            "url": item.get("url", ""),
                            "symbols": item.get("symbols", [symbol]),
                            "created_at": item.get("created_at", ""),
                        }
                        for item in raw_news
                    ]
        except Exception:
            pass

        return []
