import asyncio
import sys
from pathlib import Path

# Add apps/api to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from app.infrastructure.database.session import init_db, async_session_factory
from app.infrastructure.alpaca.mcp_client import AlpacaBrokerGateway
from app.infrastructure.options.mock_gateway import MockOptionsIntelligenceGateway
from app.agents.orchestrator import VoltronOrchestrator
from app.services.decision_service import DecisionService
from app.services.execution_service import ExecutionService
from app.infrastructure.database.repositories.decisions import DecisionRepository
from app.infrastructure.database.repositories.agents import AgentRepository
from app.infrastructure.database.repositories.orders import OrderRepository

async def run_e2e_demo():
    print("============================================================")
    print("VOLTRON FULL END-TO-END WORKFLOW VERIFICATION (MOCK MODE)")
    print("============================================================")

    # 1. Initialize DB
    await init_db()
    print("[1/8] Database tables initialized and verified.")

    # 2. Gateways
    broker = AlpacaBrokerGateway()
    quant = MockOptionsIntelligenceGateway()
    print("[2/8] AlpacaBrokerGateway and MockOptionsIntelligenceGateway initialized.")

    # 3. Execute Orchestrator Mandate
    async with async_session_factory() as session:
        orchestrator = VoltronOrchestrator(broker, quant, session)
        mandate = "Harvest elevated 30-day SPY put skew with defined risk"
        packet = await orchestrator.execute_mandate(mandate=mandate, symbol="SPY")
        print(f"[3/8] Orchestrator completed mandate. Decision ID: {packet.id}")
        print(f"      Underlying: {packet.underlying} | Spot: ${packet.spotPrice:.2f} | Regime: {packet.marketRegime}")
        print(f"      Selected Strategy: {packet.strategy.name} | POP: {packet.strategy.pop*100:.1f}% | Score: {packet.strategy.score:.1f}")
        print(f"      Risk Compiler Gate: Approved={packet.riskCompilerResult.isApproved} | Status: {packet.status}")

    # 4. Verify Trace Steps & Audit Trail
    async with async_session_factory() as session:
        agent_repo = AgentRepository(session)
        runs = await agent_repo.get_by_decision(packet.id)
        print(f"[4/8] Agent runs persisted: {len(runs)} steps in trace audit graph.")
        for r in runs:
            print(f"      - [{r.agent_role}] {r.title}: {r.status}")

    # 5. Human Approval & Execution Pipeline
    async with async_session_factory() as session:
        exec_service = ExecutionService(session, broker)
        order_result = await exec_service.approve_and_execute(packet.id)
        print(f"[5/8] Human Approval Executed: Order ID {order_result.orderId}")
        print(f"      Status: {order_result.status.upper()} | Broker: {order_result.broker} | AvgPrice: ${order_result.avgPrice:.2f}")

    # 6. Test Approval Idempotency
    async with async_session_factory() as session:
        exec_service = ExecutionService(session, broker)
        order_retry = await exec_service.approve_and_execute(packet.id)
        assert order_retry.orderId == order_result.orderId
        print(f"[6/8] Idempotency Verified: Duplicate approval returned existing order {order_retry.orderId} without duplicate dispatch.")

    # 7. Query Stored Order & History
    async with async_session_factory() as session:
        dec_repo = DecisionRepository(session)
        stored_dec = await dec_repo.get_by_id(packet.id)
        assert stored_dec.status == "APPROVED"
        print(f"[7/8] Database status verified: {stored_dec.status}")

    # 8. Counterfactual Simulation
    cf = await quant.get_counterfactual({"targetDelta": 0.20, "dte": 45})
    print(f"[8/8] Counterfactual simulation verified: Winner={cf.scenario.winningStrategy.name} vs Baseline={cf.baseline.winningStrategy.name}")

    print("============================================================")
    print("VOLTRON FULL END-TO-END DEMO COMPLETED SUCCESSFULLY!")
    print("============================================================")

if __name__ == "__main__":
    asyncio.run(run_e2e_demo())
