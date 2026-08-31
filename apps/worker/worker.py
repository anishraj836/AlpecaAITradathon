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
        logger.info("Voltron Autonomous Worker background daemon started.")
        watchlist = ["SPY", "QQQ", "NVDA", "AAPL"]

        while self.is_running:
            try:
                clock = await self.broker.get_clock()
                is_open = clock.get("is_open", False)

                if not is_open:
                    next_open = clock.get("next_open", "09:30 EST")
                    logger.info(f"Market is CLOSED (Next Open: {next_open}). Background loop paused. Sleeping 60s...")
                    await asyncio.sleep(60)
                    continue

                logger.info("Market is OPEN. Executing automated watchlist scanning...")
                for sym in watchlist:
                    if not self.is_running:
                        break
                    mandate_text = f"Harvest elevated put skew on {sym} with defined risk"
                    logger.info(f"Worker processing mandate for {sym}...")
                    await self.process_mandate(mandate=mandate_text, symbol=sym)
                    await asyncio.sleep(10)

                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error in worker run_loop: {e}", exc_info=True)
                await asyncio.sleep(30)

if __name__ == "__main__":
    worker = VoltronAnalysisWorker()
    asyncio.run(worker.run_loop())
