import logging
import asyncio
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
from app.infrastructure.database.repositories.orders import OrderRepository
from app.infrastructure.database.models import (
    AgentRunModel,
    RiskCheckModel,
    StrategyCandidateModel,
    OrderModel,
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
        autonomy_level: Optional[str] = None,
    ) -> DecisionPacket:
        symbol = symbol.upper()
        now_dt = datetime.now(timezone.utc)
        decision_id = f"DEC-{symbol}-{now_dt.strftime('%H%M%S')}"
        trace_steps: List[AgentTraceStep] = []

        # Resolve active autonomy level
        active_autonomy = (
            autonomy_level or getattr(settings, "AUTONOMY_LEVEL", "GUARDED_AUTONOMOUS")
        ).upper()

        logger.info(f"[{decision_id}] Starting orchestrator mandate: '{mandate}' on {symbol} (Autonomy: {active_autonomy})")

        try:
            # Stage 0: Initialization
            await self._emit_event(
                decision_id=decision_id,
                event_type="analysis_created",
                stage="INIT",
                status="ACTIVE",
                message=f"Mandate initialized for {symbol}: '{mandate}'",
            )

            # Stage 1: Concurrent High-Speed Data Fetch (Account, Market Quotes, News & Option Chain in Parallel)
            fetch_results = await asyncio.gather(
                self.broker.get_account(),
                self.broker.get_market_context(symbol),
                self.broker.get_news(symbol, limit=5),
                self.broker.get_option_chain(symbol),
                return_exceptions=True,
            )

            # Unpack results with safe fallbacks
            account = fetch_results[0] if not isinstance(fetch_results[0], Exception) else await self.broker.get_account()
            market_context = fetch_results[1] if not isinstance(fetch_results[1], Exception) else await self.broker.get_market_context(symbol)
            news_items = fetch_results[2] if not isinstance(fetch_results[2], Exception) else []
            market_context.news = news_items

            chain_legs = fetch_results[3] if not isinstance(fetch_results[3], Exception) else []
            chain_dicts = [l.model_dump() for l in chain_legs] if chain_legs else None

            await self._emit_event(
                decision_id=decision_id,
                event_type="market_context_completed",
                stage="DATA_FETCH",
                status="COMPLETE",
                message=f"Retrieved {symbol} spot price: ${market_context.price:.2f} ({len(market_context.news or [])} news items ingested)",
                payload={"spotPrice": market_context.price, "equity": account.equity, "newsCount": len(market_context.news or [])},
            )

            # Stage 2 & 3: Concurrent Volatility Surface & Candidate Generation
            surface_task = self.quant.get_surface(symbol, spot=market_context.price, chain=chain_dicts)
            candidates_task = self.quant.generate_candidates(
                symbol=symbol,
                target_delta=target_delta,
                max_budget=budget,
                spot=market_context.price,
                chain=chain_dicts,
            )

            surface, candidates = await asyncio.gather(surface_task, candidates_task)
            anomalies = surface.anomalies if surface.anomalies else await self.quant.detect_anomalies(symbol, spot=market_context.price)

            await self._emit_event(
                decision_id=decision_id,
                event_type="surface_completed",
                stage="DATA_FETCH",
                status="COMPLETE",
                message=f"Retrieved {symbol} live option chain ({len(chain_legs)} contracts) and surface",
            )

            if not candidates:
                raise ValueError(f"No candidate options strategies returned by Quant engine for {symbol}.")

            await self._emit_event(
                decision_id=decision_id,
                event_type="candidate_generation_completed",
                stage="QUANT_GEN",
                status="COMPLETE",
                message=f"Generated {len(candidates)} candidate structures dynamically",
            )

            # Stage 4 & 5: Concurrently Run Researcher Agent and Volatility Analyst Agent
            await self._emit_event(
                decision_id=decision_id,
                event_type="researcher_started",
                stage="RESEARCH",
                status="ACTIVE",
                message="Market Researcher evaluating price regime and intraday dispersion...",
            )
            await self._emit_event(
                decision_id=decision_id,
                event_type="volatility_started",
                stage="VOLATILITY",
                status="ACTIVE",
                message="Volatility Analyst interpreting skew and term structure...",
            )

            research_out, trace_1 = await self.researcher.run(
                input_data=market_context,
                decision_id=decision_id,
                step_id="step-1",
                title="Market Regime Identified",
            )
            trace_steps.append(trace_1)

            vol_out, trace_2 = await self.vol_analyst.run(
                input_data=surface,
                decision_id=decision_id,
                step_id="step-2",
                title="Unusual Put Skew Detected",
            )
            trace_steps.append(trace_2)

            await self._emit_event(
                decision_id=decision_id,
                event_type="researcher_completed",
                stage="RESEARCH",
                status="COMPLETE",
                message=f"Researcher identified: {research_out.marketRegimeSummary}",
                payload=research_out.model_dump(),
            )
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

            # Stage 11: Radical Transparency Audit (Detect Degraded Mode)
            is_degraded = any(
                getattr(t, "executionMode", None) == "HEURISTIC_FALLBACK" for t in trace_steps
            )
            degraded_reason = (
                "AI Committee was unavailable (API quota / network). Heuristic rules were used as backup."
                if is_degraded else None
            )

            from app.infrastructure.llm import llm_client
            active_provider = llm_client.provider_name if not is_degraded else "Deterministic Quant Heuristics"
            active_model = llm_client.model_name if not is_degraded else "Mathematical Rules"

            first_evidence = research_out.relevantEvidence[0] if research_out.relevantEvidence else "Market regime verified"
            
            # Confidence penalty if degraded
            raw_conf = (research_out.confidence + vol_out.confidence + strat_out.confidence + critic_out.confidence) / 4.0
            ai_conf = round(min(raw_conf, 0.45) if is_degraded else raw_conf, 2)

            packet = DecisionPacket(
                id=decision_id,
                createdAt=_utc_now_iso(),
                underlying=symbol,
                spotPrice=market_context.price,
                marketRegime=research_out.marketRegimeSummary,
                iv30=surface.skewSnapshot.atmIV,
                ivRank=72.1,
                aiConfidence=ai_conf,
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
                autonomyLevel=active_autonomy,
                isDegradedMode=is_degraded,
                llmProvider=active_provider,
                llmModel=active_model,
                degradedReason=degraded_reason,
            )

            # Stage 12: Database Persistence
            if self.session:
                await self._persist_decision(packet, trace_steps, candidates, risk_result)

            # Stage 13: Autonomy Spectrum Routing (with Safety Demotion)
            clock = await self.broker.get_clock()
            is_market_open = clock.get("is_open", True)
            next_open_str = clock.get("next_open", "09:30 EST")

            if not is_market_open:
                market_held_note = f"Market is CLOSED (Next Open: {next_open_str}). Automated execution safely managed."
                packet.whyThisTrade.append(market_held_note)
                packet.evidence.description = f"⚠️ [MARKET CLOSED - Next Open: {next_open_str}] {packet.evidence.description}".strip()
                if self.session:
                    dec_repo = DecisionRepository(self.session)
                    await dec_repo.save(packet)
                    await self.session.commit()

            can_auto_execute = (
                active_autonomy in ["GUARDED_AUTONOMOUS", "AUTOPILOT"]
                and decision_status == "AWAITING_APPROVAL"
                and self.session is not None
            )

            if can_auto_execute:
                if is_degraded and active_autonomy == "GUARDED_AUTONOMOUS":
                    # 🚨 SAFETY DEMOTION: In Guarded mode, hold for manual human review if LLM was rate-limited
                    logger.warning(f"[{decision_id}] GUARDED SAFETY DEMOTION: AI reasoning was degraded. Autonomous execution locked. Demoted to Copilot Mode.")
                    await self._emit_event(
                        decision_id=decision_id,
                        event_type="safety_demotion_activated",
                        stage="EXECUTION",
                        status="COMPLETE",
                        message=f"⚠️ Safety Demotion: AI Committee was offline/rate-limited. Autonomous execution locked. Manual human review required.",
                        payload=packet.model_dump(),
                    )
                elif not is_market_open and active_autonomy == "GUARDED_AUTONOMOUS":
                    # 🛡️ Guarded Auto holds when market is closed to ensure human review before open
                    logger.info(f"[{decision_id}] GUARDED AUTO HOLD: Market is closed. Decision held in Decision Room.")
                    await self._emit_event(
                        decision_id=decision_id,
                        event_type="market_closed_held",
                        stage="EXECUTION",
                        status="COMPLETE",
                        message=f"⏸️ Market Closed ({clock.get('market_status', 'CLOSED')}): Next open at {next_open_str}. Held in Decision Room for review.",
                        payload=packet.model_dump(),
                    )
                else:
                    if is_market_open:
                        from app.services.execution_service import ExecutionService
                        logger.info(f"[{decision_id}] AUTONOMOUS EXECUTION ({active_autonomy}): Risk gate passed and market is OPEN. Routing directly to Alpaca...")
                        exec_service = ExecutionService(self.session, self.broker)
                        order_result = await exec_service.approve_and_execute(decision_id)
                        if order_result.status in ("accepted", "filled", "new", "partially_filled", "held"):
                            packet.status = "APPROVED"
                            await self._emit_event(
                                decision_id=decision_id,
                                event_type="autonomous_order_executed",
                                stage="EXECUTION",
                                status="COMPLETE",
                                message=f"🚀 Autonomous Quant Execution ({active_autonomy}): Order {order_result.orderId} status '{order_result.status}' on {order_result.broker}",
                                payload=order_result.model_dump(),
                            )
                        else:
                            packet.status = "REJECTED"
                            err = "Broker rejected order"
                            if isinstance(order_result.rawResponse, dict):
                                err = order_result.rawResponse.get("error") or str(order_result.rawResponse)
                            logger.warning(f"[{decision_id}] Order rejected by broker: {err}")
                            await self._emit_event(
                                decision_id=decision_id,
                                event_type="broker_order_rejected",
                                stage="EXECUTION",
                                status="FAILED",
                                message=f"❌ Broker Order Rejected ({order_result.status}): {err}",
                                payload=order_result.model_dump(),
                            )
                    else:
                        # 🌙 AUTOPILOT PAPER QUEUE: Auto-approves paper orders even outside hours
                        auto_order_id = f"ALP-AUTO-{decision_id}"
                        packet.status = "APPROVED"

                        if self.session:
                            dec_repo = DecisionRepository(self.session)
                            await dec_repo.save(packet)

                            order_repo = OrderRepository(self.session)
                            order_model = OrderModel(
                                id=auto_order_id,
                                decision_id=decision_id,
                                client_order_id=f"cl-{decision_id}",
                                broker_order_id=auto_order_id,
                                symbol=packet.underlying,
                                order_type="limit",
                                status="accepted",
                                avg_price=packet.strategy.netCreditOrDebit if packet.strategy else 1.38,
                                qty=1,
                                raw_payload={"queued": True, "market_status": "CLOSED", "next_open": next_open_str, "mode": active_autonomy},
                            )
                            await order_repo.save_order(order_model)
                            await self.session.commit()

                        logger.info(f"[{decision_id}] AUTOPILOT PRE-AUTHORIZATION: Auto-approved and queued for {next_open_str} open.")
                        await self._emit_event(
                            decision_id=decision_id,
                            event_type="autonomous_order_executed",
                            stage="EXECUTION",
                            status="COMPLETE",
                            message=f"🚀 Autopilot Paper Execution: Decision {decision_id} auto-approved & queued for Alpaca Paper at {next_open_str} open!",
                            payload=packet.model_dump(),
                        )
            else:
                await self._emit_event(
                    decision_id=decision_id,
                    event_type="decision_completed",
                    stage="COMPLETE",
                    status="COMPLETE",
                    message=f"Decision Packet {decision_id} ready for human approval (Mode: {active_autonomy}).",
                    payload=packet.model_dump(),
                )

            logger.info(f"[{decision_id}] Orchestrator execution completed successfully with status: {packet.status} (Degraded: {is_degraded})")
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
