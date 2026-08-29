import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.domain.models import DecisionPacket
from app.infrastructure.alpaca.mcp_client import AlpacaBrokerGateway
from app.infrastructure.options.mock_gateway import MockOptionsIntelligenceGateway
from app.infrastructure.database.session import async_session_factory, init_db
from app.agents.orchestrator import VoltronOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VoltronWorker")

class VoltronAnalysisWorker:
    """
    Asynchronous analysis worker consuming and executing mandates through VoltronOrchestrator.
    """

    def __init__(self):
        self.broker = AlpacaBrokerGateway()
        self.quant = MockOptionsIntelligenceGateway()
        self.is_running = False

    async def process_mandate(
        self,
        mandate: str,
        symbol: str = "SPY",
        target_delta: float = 0.15,
        budget: float = 50000.0,
    ) -> DecisionPacket:
        await init_db()
        async with async_session_factory() as session:
            orchestrator = VoltronOrchestrator(
                broker_gateway=self.broker,
                quant_gateway=self.quant,
                session=session,
            )
            packet = await orchestrator.execute_mandate(
                mandate=mandate,
                symbol=symbol,
                target_delta=target_delta,
                budget=budget,
            )
            return packet

    async def run_loop(self):
        self.is_running = True
        await init_db()
        logger.info("Voltron Worker background loop started.")
        while self.is_running:
            await asyncio.sleep(60)

if __name__ == "__main__":
    worker = VoltronAnalysisWorker()
    asyncio.run(worker.run_loop())
