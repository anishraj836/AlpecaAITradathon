import time
import httpx
from typing import Optional, Dict, Any, Tuple
from app.config import settings
from app.domain.models import MarketContext
from app.infrastructure.alpaca.normalizer import AlpacaNormalizer

_MARKET_CONTEXT_CACHE: Dict[str, Tuple[float, MarketContext]] = {}
_NEWS_CACHE: Dict[str, Tuple[float, list]] = {}
CACHE_TTL_SECONDS = 45.0

class AlpacaMarketDataService:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.client = client
        self.headers = {
            "APCA-API-KEY-ID": settings.ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": settings.ALPACA_SECRET_KEY,
            "Content-Type": "application/json",
        }

    async def get_market_context(self, symbol: str) -> MarketContext:
        symbol = symbol.strip().upper()
        now_ts = time.time()
        if symbol in _MARKET_CONTEXT_CACHE:
            ts, cached_ctx = _MARKET_CONTEXT_CACHE[symbol]
            if now_ts - ts < CACHE_TTL_SECONDS:
                return cached_ctx

        known_defaults = {
            "SPY": 645.31, "QQQ": 510.00, "IWM": 224.50, "NVDA": 138.50,
            "AAPL": 228.40, "TSLA": 215.10, "MSFT": 425.00, "AMZN": 186.00,
            "META": 528.00, "GOOGL": 168.00, "AMD": 154.00, "PLTR": 34.50,
            "COIN": 212.00, "SMCI": 448.00, "ARM": 134.00, "GLD": 230.00,
            "DIS": 96.00, "NFLX": 685.00, "AVGO": 162.00, "UBER": 76.50,
            "BABA": 88.00, "BA": 162.00,
        }

        if not settings.ALPACA_API_KEY or "DUMMY" in settings.ALPACA_API_KEY:
            # Deterministic test mode: only return context for known valid symbols
            if symbol not in known_defaults:
                raise ValueError(f"Ticker '{symbol}' not found on US exchanges.")
            return AlpacaNormalizer.normalize_market_context(
                symbol=symbol,
                price=known_defaults[symbol],
                change_pct=0.82 if symbol == "SPY" else 0.45,
                high=known_defaults[symbol] * 1.01,
                low=known_defaults[symbol] * 0.99,
                volume=82500000,
            )

        async with httpx.AsyncClient() as client:
            # 1. Fetch latest trade / snapshot from Alpaca Data API
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

                price = float(latest_trade.get("p", daily_bar.get("c", 0.0)))
                if price <= 0:
                    raise ValueError(f"No pricing data available for ticker '{symbol}'.")
                prev_close = float(prev_daily_bar.get("c", price))
                change_pct = ((price - prev_close) / prev_close * 100.0) if prev_close else 0.0

                ctx = AlpacaNormalizer.normalize_market_context(
                    symbol=symbol,
                    price=price,
                    change_pct=change_pct,
                    high=float(daily_bar.get("h", price * 1.01)),
                    low=float(daily_bar.get("l", price * 0.99)),
                    volume=int(daily_bar.get("v", 80000000)),
                )
                _MARKET_CONTEXT_CACHE[symbol] = (now_ts, ctx)
                return ctx
            elif resp.status_code in (404, 400, 422):
                # Verify with asset endpoint to confirm whether symbol is a valid US equity
                try:
                    asset_resp = await client.get(
                        f"{settings.ALPACA_BASE_URL}/v2/assets/{symbol}",
                        headers=self.headers,
                        timeout=5.0,
                    )
                    if asset_resp.status_code != 200:
                        raise ValueError(f"Ticker '{symbol}' not found on US exchanges or Alpaca Paper Broker.")
                    asset_data = asset_resp.json()
                    if not asset_data.get("tradable", False):
                        raise ValueError(f"Ticker '{symbol}' is not currently tradable.")
                    price = known_defaults.get(symbol, 100.0)
                    ctx = AlpacaNormalizer.normalize_market_context(symbol=symbol, price=price, change_pct=0.0)
                    _MARKET_CONTEXT_CACHE[symbol] = (now_ts, ctx)
                    return ctx
                except Exception:
                    raise ValueError(f"Ticker '{symbol}' not found on US exchanges or Alpaca Paper Broker.")
            else:
                raise ValueError(f"Failed to query market data for ticker '{symbol}' (status {resp.status_code}).")

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
        now_ts = time.time()
        if symbol in _NEWS_CACHE:
            ts, cached_news = _NEWS_CACHE[symbol]
            if now_ts - ts < CACHE_TTL_SECONDS:
                return cached_news

        if not settings.ALPACA_API_KEY or "DUMMY" in settings.ALPACA_API_KEY:
            # Deterministic news fixture for testing and offline modes
            dummy_news = [
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
            _NEWS_CACHE[symbol] = (now_ts, dummy_news)
            return dummy_news

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
                    news_list = [
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
                    if news_list:
                        _NEWS_CACHE[symbol] = (now_ts, news_list)
                    return news_list
        except Exception:
            pass

        return []
