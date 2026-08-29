from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_db_session
from app.infrastructure.alpaca.gateway import BrokerGateway
from app.infrastructure.alpaca.mcp_client import AlpacaBrokerGateway
from app.infrastructure.options.gateway import OptionsIntelligenceGateway
from app.infrastructure.options.mock_gateway import MockOptionsIntelligenceGateway
from app.infrastructure.options.mcp_client import VoltronOptionsMCPClient
from app.config import settings

# Singletons for gateways
_broker_gateway = AlpacaBrokerGateway()
_quant_gateway = MockOptionsIntelligenceGateway() if settings.USE_MOCK_QUANT else VoltronOptionsMCPClient()

def get_broker_gateway() -> BrokerGateway:
    return _broker_gateway

def get_quant_gateway() -> OptionsIntelligenceGateway:
    return _quant_gateway
