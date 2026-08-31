from typing import List, Optional
import logging
from app.infrastructure.alpaca.gateway import BrokerGateway
from app.infrastructure.alpaca.account import AlpacaAccountService
from app.infrastructure.alpaca.market_data import AlpacaMarketDataService
from app.infrastructure.alpaca.options import AlpacaOptionsService
from app.infrastructure.alpaca.trading import AlpacaTradingService
from app.infrastructure.alpaca.official_mcp_client import AlpacaOfficialMCPClient
from app.infrastructure.alpaca.normalizer import AlpacaNormalizer
from app.config import settings
from app.domain.models import (
    AccountInfo,
    PositionInfo,
    MarketContext,
    OptionLeg,
    OrderResult,
    DecisionPacket,
    MlegOrderPayload,
)

logger = logging.getLogger("AlpacaBrokerGateway")

class AlpacaBrokerGateway(BrokerGateway):
    """
    Concrete BrokerGateway implementation backed by verified Alpaca REST API,
    official alpaca-py SDK, and official Alpaca MCP tooling.
    """

    def __init__(self):
        self.account_service = AlpacaAccountService()
        self.market_service = AlpacaMarketDataService()
        self.options_service = AlpacaOptionsService()
        self.trading_service = AlpacaTradingService()
        self.mcp_client = AlpacaOfficialMCPClient()

    async def get_account(self) -> AccountInfo:
        # 1. Try official MCP protocol if active
        try:
            mcp_data = await self.mcp_client.get_account_via_mcp()
            if mcp_data and "equity" in mcp_data:
                return AlpacaNormalizer.normalize_account(mcp_data, is_paper=settings.ALPACA_PAPER)
        except Exception:
            pass

        # 2. Fall back to official alpaca-py SDK & REST
        return await self.account_service.get_account()

    async def get_positions(self) -> List[PositionInfo]:
        # 1. Try official MCP protocol if active
        try:
            mcp_positions = await self.mcp_client.get_positions_via_mcp()
            if mcp_positions and isinstance(mcp_positions, list):
                return AlpacaNormalizer.normalize_positions(mcp_positions)
        except Exception:
            pass

        # 2. Fall back to official alpaca-py SDK & REST
        return await self.account_service.get_positions()

    async def get_market_context(self, symbol: str) -> MarketContext:
        return await self.market_service.get_market_context(symbol)

    async def get_option_chain(
        self,
        symbol: str,
        expiration_gte: Optional[str] = None,
        expiration_lte: Optional[str] = None,
    ) -> List[OptionLeg]:
        return await self.options_service.get_option_chain(symbol, expiration_gte, expiration_lte)

    async def place_multileg_order(
        self,
        decision: DecisionPacket,
        order_payload: Optional[MlegOrderPayload] = None,
    ) -> OrderResult:
        return await self.trading_service.place_multileg_order(decision, order_payload)

    async def get_order(self, order_id: str) -> OrderResult:
        return await self.trading_service.get_order(order_id)
