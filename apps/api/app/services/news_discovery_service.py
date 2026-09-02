import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.infrastructure.alpaca.gateway import BrokerGateway

logger = logging.getLogger("NewsDiscoveryService")

CATALYST_KEYWORDS = [
    "earnings", "guidance", "surge", "drop", "plunge", "rally", "breakout",
    "options", "upgrade", "downgrade", "acquisition", "deal", "revenue",
    "fda", "antitrust", "soars", "slumps", "target", "patent", "merger",
    "short squeeze", "calls", "puts", "investigation", "ceo", "ai", "chips",
    "contract", "record", "jump", "crash", "tumble", "reiterates", "skyrockets"
]

CRYPTO_FILTER = {"BTC", "ETH", "USDT", "SOL", "XRP", "DOGE", "ADA", "AVAX"}

class DiscoveredTicker(BaseModel):
    symbol: str
    headline: str
    source: str
    catalystKeywords: List[str] = Field(default_factory=list)
    confidenceScore: float
    optionContractsCount: int
    discoveredAt: str

class NewsDiscoveryService:
    """
    Autonomous Market Catalyst & Ticker Discovery Engine.
    Scans live breaking news feeds, identifies high-volatility catalysts,
    validates options chain liquidity on Alpaca, and extracts new candidate tickers.
    """

    def extract_catalysts(self, text: str) -> List[str]:
        lower_text = text.lower()
        return [kw for kw in CATALYST_KEYWORDS if kw in lower_text]

    async def discover_candidates(
        self,
        broker: BrokerGateway,
        existing_watchlist: List[str],
        limit: int = 30,
    ) -> List[DiscoveredTicker]:
        """
        Query broad market news, match catalyst signals, verify options liquidity,
        and return actionable discovered tickers.
        """
        existing_set = {s.upper() for s in existing_watchlist}
        articles = await broker.get_market_news(limit=limit)

        if not articles:
            logger.info("No news articles returned from market data feed.")
            return []

        # Map candidate symbol -> (best_headline, best_source, keywords, match_count)
        candidates: Dict[str, Dict[str, Any]] = {}

        for art in articles:
            headline = art.get("headline", "")
            summary = art.get("summary", "")
            source = art.get("source", "Alpaca Market Wire")
            full_text = f"{headline} {summary}"

            keywords = self.extract_catalysts(full_text)
            symbols = art.get("symbols", [])

            for raw_sym in symbols:
                sym = raw_sym.strip().upper()
                # Validation rules:
                # 1. 1-5 alphabetic chars
                if not (sym.isalpha() and 1 <= len(sym) <= 5):
                    continue
                # 2. Exclude crypto
                if sym in CRYPTO_FILTER:
                    continue
                # 3. Exclude if already in watchlist
                if sym in existing_set:
                    continue

                if sym not in candidates:
                    candidates[sym] = {
                        "symbol": sym,
                        "headline": headline,
                        "source": source,
                        "keywords": set(keywords),
                        "count": 1,
                    }
                else:
                    candidates[sym]["count"] += 1
                    candidates[sym]["keywords"].update(keywords)
                    if len(headline) > len(candidates[sym]["headline"]):
                        candidates[sym]["headline"] = headline
                        candidates[sym]["source"] = source

        if not candidates:
            return []

        # Sort candidate tickers by catalyst keyword relevance and news frequency
        ranked = sorted(
            candidates.values(),
            key=lambda c: (len(c["keywords"]) * 2 + c["count"]),
            reverse=True,
        )

        discovered: List[DiscoveredTicker] = []
        now_str = datetime.now(timezone.utc).strftime("%H:%M:%S")

        # Verify options liquidity for top candidates (limit to top 4 to avoid rate limits)
        for cand in ranked[:5]:
            sym = cand["symbol"]
            try:
                chain = await broker.get_option_chain(sym)
                chain_len = len(chain)
                # Must have at least 10 active option contracts on Alpaca
                if chain_len >= 10:
                    keywords_list = list(cand["keywords"])
                    score = min(0.98, 0.60 + len(keywords_list) * 0.08 + (0.05 if chain_len >= 100 else 0.0))
                    discovered.append(
                        DiscoveredTicker(
                            symbol=sym,
                            headline=cand["headline"],
                            source=cand["source"],
                            catalystKeywords=keywords_list,
                            confidenceScore=round(score, 2),
                            optionContractsCount=chain_len,
                            discoveredAt=now_str,
                        )
                    )
            except Exception as e:
                logger.debug(f"Error checking option chain for {sym}: {e}")

        return discovered

news_discovery_service = NewsDiscoveryService()
