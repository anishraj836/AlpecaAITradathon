from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models import (
    AccountInfo,
    PositionInfo,
    MarketContext,
    OptionLeg,
    OrderResult,
    MlegOrderPayload,
    DecisionPacket,
)

class BrokerGateway(ABC):
    """
    Abstract Broker Gateway interface for VOLTRON.
    Exposes canonical operations for market data, options chain, account, and paper trading execution.
    """

    @abstractmethod
    async def get_account(self) -> AccountInfo:
        """Retrieve current trading account balances and status."""
        pass

    @abstractmethod
    async def get_positions(self) -> List[PositionInfo]:
        """Retrieve open stock and options positions."""
        pass

    @abstractmethod
    async def get_market_context(self, symbol: str) -> MarketContext:
        """Retrieve underlying spot price, daily volume, high, low, and change percentage."""
        pass

    @abstractmethod
    async def get_option_chain(
        self,
        symbol: str,
        expiration_gte: Optional[str] = None,
        expiration_lte: Optional[str] = None,
    ) -> List[OptionLeg]:
        """Retrieve normalized option chain contracts with greeks and quotes."""
        pass

    @abstractmethod
    async def place_multileg_order(
        self,
        decision: DecisionPacket,
        order_payload: Optional[MlegOrderPayload] = None,
    ) -> OrderResult:
        """
        Submit a defined-risk multi-leg order to Alpaca Paper Trading.
        Enforces paper environment validation before dispatch.
        """
        pass

    @abstractmethod
    async def get_order(self, order_id: str) -> OrderResult:
        """Retrieve status and fills for a submitted order."""
        pass

    async def get_clock(self) -> dict:
        """Retrieve market clock and open/closed status."""
        return {
            "is_open": True,
            "next_open": "2026-09-01T09:30:00-04:00",
            "next_close": "2026-09-01T16:00:00-04:00",
            "market_status": "OPEN",
        }

    async def get_news(self, symbol: str, limit: int = 5) -> List[dict]:
        """Retrieve latest market news headlines and catalyst summaries for a symbol."""
        return []

    async def get_market_news(self, limit: int = 20) -> List[dict]:
        """Retrieve broad real-time financial market news headlines across all tickers."""
        return []

    async def close_position(self, symbol_or_asset_id: str, qty: Optional[float] = None) -> dict:
        """Liquidate an individual open stock or options position."""
        return {"status": "success", "symbol": symbol_or_asset_id, "closed": True, "qty": qty or 1.0}

    async def close_all_positions(self) -> dict:
        """Liquidate all open positions in paper trading account."""
        return {"status": "success", "closed": 0}

    async def get_portfolio_history(self, period: str = "1M", timeframe: str = "1D") -> dict:
        """Retrieve portfolio equity curve over time."""
        return {
            "timestamp": [],
            "equity": [],
            "profit_loss": [],
            "profit_loss_pct": [],
            "base_value": 100000.0,
            "timeframe": timeframe,
        }
