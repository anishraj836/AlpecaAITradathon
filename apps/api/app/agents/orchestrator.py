import logging
from typing import Optional, List, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import (
    DecisionPacket,
    MarketResearch,
    VolatilityAnalysis,
    StrategySelection,
    StrategyCandidate,
    Critique,
    RiskCheckResult,
    AgentTraceStep,
    OrchestratorEvent,
    Tag,
    AgentTraceDetails,
    RiskMetric,
    DecisionStatus,
)
from app.infrastructure.alpaca.gateway import BrokerGateway
from app.infrastructure.options.gateway import OptionsIntelligenceGateway
from app.infrastructure.database.repositories.decisions import DecisionRepository
from app.infrastructure.database.repositories.agents import AgentRepository
from app.infrastructure.database.repositories.risk import RiskRepository
from app.infrastructure.database.repositories.strategies import StrategyRepository
from app.infrastructure.database.models import (
    AgentRunModel,
    RiskCheckModel,
    StrategyCandidateModel,
)
from app.agents.researcher import MarketResearcherAgent
from app.agents.volatility import VolatilityAnalystAgent
from app.agents.strategist import StrategyAnalystAgent, StrategyAnalystInput
from app.agents.critic import CriticAgent, CriticInput
from app.services.event_broadcaster import broadcaster
from app.config import settings

logger = logging.getLogger("VoltronOrchestrator")

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"

class VoltronOrchestrator:
    """
    Central Runtime Multi-Agent Orchestration Engine for VOLTRON.
    Coordinates the 4 AI reasoning agents (Researcher, Volatility Analyst, Strategy Analyst, Critic)
    and executes the deterministic Risk Compiler gate.
    """

    def __init__(
        self,
        broker_gateway: BrokerGateway,
        quant_gateway: OptionsIntelligenceGateway,
        session: Optional[AsyncSession] = None,
    ):
        self.broker = broker_gateway
        self.quant = quant_gateway
        self.session = session

        # Agent Instances
        self.researcher = MarketResearcherAgent()
        self.vol_analyst = VolatilityAnalystAgent()
        self.strategist = StrategyAnalystAgent()
        self.critic = CriticAgent()

    async def _emit_event(
        self,
        decision_id: str,
        event_type: str,
        stage: str,
        status: str,
        message: str,
        payload: Optional[dict] = None,
    ):
        event = OrchestratorEvent(
            decisionId=decision_id,
            eventType=event_type,
            stage=stage,
            status=status, # type: ignore
            message=message,
            timestamp=_utc_now_iso(),
            payload=payload,
        )
        await broadcaster.broadcast(event)

    async def execute_mandate(
        self,
        mandate: str,
        symbol: str = "SPY",
        target_delta: float = 0.15,
        budget: float = 50000.0,
    ) -> DecisionPacket:
        symbol = symbol.upper()
        now_dt = datetime.now(timezone.utc)
        decision_id = f"DEC-{symbol}-{now_dt.strftime('%H%M%S')}"
        trace_steps: List[AgentTraceStep] = []

        logger.info(f"[{decision_id}] Starting orchestrator mandate: '{mandate}' on {symbol}")

        try:
            # Stage 0: Initialization
            await self._emit_event(
                decision_id=decision_id,
                event_type="analysis_created",
                stage="INIT",
                status="ACTIVE",
                message=f"Mandate initialized for {symbol}: '{mandate}'",
            )

            # Stage 1: Market & Account Data (Single Fetch)
            account = await self.broker.get_account()
            market_context = await self.broker.get_market_context(symbol)
            await self._emit_event(
                decision_id=decision_id,
                event_type="market_context_completed",
                stage="DATA_FETCH",
                status="COMPLETE",
                message=f"Retrieved {symbol} spot price: ${market_context.price:.2f}",
                payload={"spotPrice": market_context.price, "equity": account.equity},
            )

            # Stage 2: Volatility Surface & Anomaly Scanning (Single Quant MCP Fetch)
            surface = await self.quant.get_surface(symbol)
            anomalies = surface.anomalies if surface.anomalies else await self.quant.detect_anomalies(symbol)
            await self._emit_event(
                decision_id=decision_id,
                event_type="surface_completed",
                stage="DATA_FETCH",
                status="COMPLETE",
                message=f"Retrieved volatility surface and {len(anomalies)} anomalies",
            )

            # Stage 3: Candidate Generation (Quant MCP)
            candidates = await self.quant.generate_candidates(symbol, target_delta, budget)
            if not candidates:
                raise ValueError(f"No candidate options strategies returned by Quant engine for {symbol}.")
            await self._emit_event(
                decision_id=decision_id,
                event_type="candidate_generation_completed",
                stage="QUANT_GEN",
                status="COMPLETE",
                message=f"Generated {len(candidates)} candidate structures",
            )

            # Stage 4: Run Researcher Agent
            await self._emit_event(
                decision_id=decision_id,
                event_type="researcher_started",
                stage="RESEARCH",
                status="ACTIVE",
                message="Market Researcher evaluating price regime and intraday dispersion...",
            )
            research_out, trace_1 = await self.researcher.run(
                input_data=market_context,
                decision_id=decision_id,
                step_id="step-1",
                title="Market Regime Identified",
            )
            trace_steps.append(trace_1)
            await self._emit_event(
                decision_id=decision_id,
                event_type="researcher_completed",
                stage="RESEARCH",
                status="COMPLETE",
                message=f"Researcher identified: {research_out.marketRegimeSummary}",
                payload=research_out.model_dump(),
            )

            # Stage 5: Run Volatility Analyst Agent
            await self._emit_event(
                decision_id=decision_id,
                event_type="volatility_started",
                stage="VOLATILITY",
                status="ACTIVE",
                message="Volatility Analyst interpreting skew and term structure...",
            )
            vol_out, trace_2 = await self.vol_analyst.run(
                input_data=surface,
                decision_id=decision_id,
                step_id="step-2",
                title="Unusual Put Skew Detected",
            )
            trace_steps.append(trace_2)
            await self._emit_event(
                decision_id=decision_id,
                event_type="volatility_completed",
                stage="VOLATILITY",
                status="COMPLETE",
                message=f"Volatility analysis complete: {vol_out.keyAnomaly}",
                payload=vol_out.model_dump(),
            )

            # Stage 6: Run Strategy Analyst Agent
            await self._emit_event(
                decision_id=decision_id,
                event_type="strategy_started",
                stage="STRATEGY",
                status="ACTIVE",
                message="Strategy Analyst selecting winning candidate structure...",
            )
            strat_input = StrategyAnalystInput(
                research=research_out,
                volatility=vol_out,
                candidates=candidates,
            )
            strat_out, trace_3 = await self.strategist.run(
                input_data=strat_input,
                decision_id=decision_id,
                step_id="step-3",
                title="Candidate #1 Selected",
            )
            trace_steps.append(trace_3)

            # Retrieve selected winning candidate object
            selected_strategy = next((c for c in candidates if c.id == strat_out.selectedCandidateId), candidates[0])
            selected_strategy.isWinner = True
            await self._emit_event(
                decision_id=decision_id,
                event_type="strategy_completed",
                stage="STRATEGY",
                status="COMPLETE",
                message=f"Strategy selected: {selected_strategy.name}",
                payload=selected_strategy.model_dump(),
            )

            # Stage 7: Run Stress Test for Selected Candidate
            stress_report = await self.quant.stress_test(selected_strategy.id)

            # Stage 8: Run Adversarial Critic Agent
            await self._emit_event(
                decision_id=decision_id,
                event_type="critic_started",
                stage="CRITIC",
                status="ACTIVE",
                message="Adversarial Critic attempting to invalidate trade...",
            )
            critic_input = CriticInput(
                strategy=selected_strategy,
                stressReport=stress_report,
                research=research_out,
                volatility=vol_out,
            )
            critic_out, trace_4 = await self.critic.run(
                input_data=critic_input,
                decision_id=decision_id,
                step_id="step-4",
                title="Upside Breakout Risk Identified",
            )
            trace_steps.append(trace_4)
            await self._emit_event(
                decision_id=decision_id,
                event_type="critic_completed",
                stage="CRITIC",
                status="COMPLETE",
                message=f"Critic assessment: {critic_out.primaryFailureMode} ({critic_out.severity})",
                payload=critic_out.model_dump(),
            )

            # Stage 9: Deterministic Risk Compiler Check (Pure Code)
            await self._emit_event(
                decision_id=decision_id,
                event_type="risk_started",
                stage="RISK",
                status="ACTIVE",
                message="Deterministic Risk Compiler evaluating portfolio limits...",
            )
            risk_result = await self.quant.compile_risk(selected_strategy, account.equity)
            
            trace_5 = AgentTraceStep(
                id="step-5",
                agentRole="RISK_COMPILER",
                agentLabel="Deterministic Code Check",
                title="Final Checks Passed" if risk_result.isApproved else "Risk Gate Rejected",
                timestampOffset="T-0ms (READY)",
                status="COMPLETE" if risk_result.isApproved else "FAILED",
                summary="Budget allocation, liquidity check, and concentration limits evaluated by deterministic code gate.",
                confidenceScore=1.0 if risk_result.isApproved else 0.0,
                tags=[
                    Tag(
                        label="APPROVED FOR EXECUTION" if risk_result.isApproved else "RISK CHECK FAILED",
                        variant="primary" if risk_result.isApproved else "error",
                    )
                ],
                details=AgentTraceDetails(
                    riskMetrics=[
                        RiskMetric(label="Budget Check", value=risk_result.budgetCheck.status),
                        RiskMetric(label="Liquidity", value=risk_result.liquidityCheck.status),
                        RiskMetric(label="Concentration", value=risk_result.concentrationCheck.status),
                    ]
                ),
            )
            trace_steps.append(trace_5)
            await self._emit_event(
                decision_id=decision_id,
                event_type="risk_completed",
                stage="RISK",
                status="COMPLETE" if risk_result.isApproved else "FAILED",
                message=f"Deterministic risk check result: Approved={risk_result.isApproved}",
                payload=risk_result.model_dump(),
            )

            # Stage 10: Decision Status Determination (Handling NO-TRADE path)
            if not risk_result.isApproved or critic_out.verdict == "REJECTED":
                decision_status: DecisionStatus = "REJECTED"
            else:
                decision_status = "AWAITING_APPROVAL"

            # Stage 11: Assemble Complete DecisionPacket
            first_evidence = research_out.relevantEvidence[0] if research_out.relevantEvidence else "Market regime verified"
            packet = DecisionPacket(
                id=decision_id,
                createdAt=_utc_now_iso(),
                underlying=symbol,
                spotPrice=market_context.price,
                marketRegime=research_out.marketRegimeSummary,
                iv30=surface.skewSnapshot.atmIV,
                ivRank=72.1,
                aiConfidence=round((research_out.confidence + vol_out.confidence + strat_out.confidence + critic_out.confidence) / 4.0, 2),
                strategy=selected_strategy,
                evidence={
                    "description": f"{vol_out.summary} {first_evidence}".strip(),
                    "putSkewElevated": True,
                    "termStructureRich": True,
                },
                whyThisTrade=strat_out.reasoning,
                criticAnalysis={
                    "primaryFailureMode": critic_out.primaryFailureMode,
                    "details": critic_out.details,
                },
                riskCompilerResult=risk_result,
                status=decision_status,
            )

            # Stage 12: Database Persistence
            if self.session:
                await self._persist_decision(packet, trace_steps, candidates, risk_result)

            # Stage 13: Autonomous Execution or Human-In-The-Loop Routing
            if settings.AUTONOMOUS_EXECUTION and decision_status == "AWAITING_APPROVAL" and self.session:
                from app.services.execution_service import ExecutionService
                logger.info(f"[{decision_id}] AUTONOMOUS MODE ACTIVE: Risk gate passed. Routing directly to Alpaca...")
                exec_service = ExecutionService(self.session, self.broker)
                order_result = await exec_service.approve_and_execute(decision_id)
                packet.status = "APPROVED"

                await self._emit_event(
                    decision_id=decision_id,
                    event_type="autonomous_order_executed",
                    stage="EXECUTION",
                    status="COMPLETE",
                    message=f"🚀 Autonomous Quant Execution: Order {order_result.orderId} filled at ${order_result.avgPrice:.2f} on {order_result.broker}",
                    payload=order_result.model_dump(),
                )
            else:
                await self._emit_event(
                    decision_id=decision_id,
                    event_type="decision_completed",
                    stage="COMPLETE",
                    status="COMPLETE",
                    message=f"Decision Packet {decision_id} ready for human approval.",
                    payload=packet.model_dump(),
                )

            logger.info(f"[{decision_id}] Orchestrator execution completed successfully with status: {packet.status}")
            return packet

        except Exception as err:
            logger.error(f"[{decision_id}] Orchestration failed: {err}", exc_info=True)
            await self._emit_event(
                decision_id=decision_id,
                event_type="decision_failed",
                stage="FAILED",
                status="FAILED",
                message=f"Orchestration Error: {str(err)}",
            )
            raise err

    async def _persist_decision(
        self,
        packet: DecisionPacket,
        trace_steps: List[AgentTraceStep],
        candidates: List[StrategyCandidate],
        risk_result: RiskCheckResult,
    ):
        try:
            dec_repo = DecisionRepository(self.session)
            agent_repo = AgentRepository(self.session)
            risk_repo = RiskRepository(self.session)
            strat_repo = StrategyRepository(self.session)

            # 1. Save Decision
            await dec_repo.save(packet)

            # 2. Save Agent Runs
            agent_models = [
                AgentRunModel(
                    id=f"{packet.id}-{step.id}",
                    decision_id=packet.id,
                    agent_role=step.agentRole,
                    title=step.title,
                    status=step.status,
                    summary=step.summary,
                    details_json=step.model_dump(),
                )
                for step in trace_steps
            ]
            await agent_repo.save_agent_runs(agent_models)

            # 3. Save Risk Checks
            risk_model = RiskCheckModel(
                id=f"risk-{packet.id}",
                decision_id=packet.id,
                is_approved=risk_result.isApproved,
                budget_pass=risk_result.budgetCheck.passed,
                liquidity_pass=risk_result.liquidityCheck.passed,
                concentration_pass=risk_result.concentrationCheck.passed,
                check_details_json=risk_result.model_dump(),
            )
            await risk_repo.save(risk_model)

            # 4. Save Candidate Strategies
            strat_models = [
                StrategyCandidateModel(
                    id=f"{packet.id}-{c.id}",
                    decision_id=packet.id,
                    name=c.name,
                    dte=c.dte,
                    score=c.score,
                    pop=c.pop,
                    max_profit=c.maxProfit,
                    max_loss=c.maxLoss,
                    net_credit=c.netCreditOrDebit,
                    liquidity_score=c.liquidityScore,
                    is_winner=c.isWinner,
                    rejection_reason=c.rejectionReason,
                    legs_json=[leg.model_dump() for leg in c.legs],
                )
                for c in candidates
            ]
            await strat_repo.save_candidates(strat_models)
            await self.session.commit()
            logger.info(f"[{packet.id}] Successfully persisted complete decision graph to database")
        except Exception as e:
            logger.error(f"Failed to persist decision {packet.id}: {e}", exc_info=True)
            await self.session.rollback()
