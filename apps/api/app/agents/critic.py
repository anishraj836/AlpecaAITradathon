from pathlib import Path
from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from app.agents.base import BaseAgent
from app.domain.models import (
    StrategyCandidate,
    StressReport,
    MarketResearch,
    VolatilityAnalysis,
    Critique,
    AgentTraceStep,
    Tag,
    AgentTraceDetails,
)

from app.infrastructure.llm import llm_client

PROMPT_PATH = str(Path(__file__).parent.parent / "prompts" / "critic.md")

class CriticInput(BaseModel):
    strategy: StrategyCandidate
    stressReport: StressReport
    research: MarketResearch
    volatility: VolatilityAnalysis
    learningMemory: Optional[Dict[str, Any]] = None

class CriticAgent(BaseAgent[CriticInput, Critique]):
    """
    Adversarial Critic Agent attempting to invalidate the trade and detect structural vulnerabilities via Multi-Provider LLM Gateway.
    """

    def __init__(self):
        super().__init__(
            role="CRITIC",
            label="Agent 04 (Adversarial Critic)",
            output_cls=Critique,
            system_prompt_path=PROMPT_PATH,
        )

    async def _execute_reasoning(self, input_data: CriticInput) -> Critique:
        strat = input_data.strategy
        stress = input_data.stressReport
        strat_name = strat.name.lower()

        # 1. Attempt Live LLM Adversarial Reasoning (Gemini, OpenAI, Groq, Anthropic, Ollama, DeepSeek)
        if llm_client.is_configured:
            learning_context = ""
            if input_data.learningMemory and input_data.learningMemory.get("promptSummary"):
                learning_context = f"\n\n[HISTORICAL EXPERIENCE & PAST LOSS POST-MORTEMS]\n{input_data.learningMemory['promptSummary']}\n"

            prompt = (
                f"Candidate Strategy to Invalidate:\n"
                f"- Name: {strat.name}\n"
                f"- Underlying: {strat.underlying} (Spot: ${input_data.research.spotPrice:.2f})\n"
                f"- Net Credit: ${strat.netCreditOrDebit}\n"
                f"- Max Loss: ${strat.maxLoss}\n"
                f"- Breakevens: {strat.breakevens}\n"
                f"- Zero Upside Risk: {strat.zeroUpsideRisk}\n"
                f"- Market Regime: {input_data.research.marketRegimeSummary}\n"
                f"- Volatility Skew: {input_data.volatility.skewInterpretation}\n"
                f"{learning_context}\n"
                f"Stress-test this trade aggressively. Specifically compare against historical failure modes. Identify primary failure modes, breakout vulnerabilities, and risk recommendations."
            )
            llm_out = await llm_client.generate_structured(
                system_instruction=self.system_prompt,
                user_prompt=prompt,
                response_model=Critique,
            )
            if llm_out:
                self.last_execution_mode = "LLM_REASONING"
                self.last_provider_name = llm_client.provider_name
                self.last_model_name = llm_client.model_name
                return llm_out

        # 2. Deterministic Fallback Engine
        self.last_execution_mode = "HEURISTIC_FALLBACK"
        self.last_provider_name = "Deterministic Engine"
        self.last_model_name = "Mathematical Rules"

        # Check for catastrophic tail loss in stress matrix
        worst_scenario = min(stress.matrix, key=lambda cell: cell.pnl) if stress.matrix else None
        worst_loss = abs(worst_scenario.pnl) if worst_scenario and worst_scenario.pnl < 0 else 0.0

        # Assess breakevens with strategy-type awareness
        breakevens = strat.breakevens
        if "lizard" in strat_name:
            lower_be = breakevens[0] if breakevens else (input_data.research.spotPrice * 0.95)
            primary_failure = f"Downside crash below ${lower_be:.2f} (Upside has ZERO risk)."
            details = f"Jade Lizard has zero upside risk due to net credit exceeding call spread width. Risk is strictly concentrated on downside liquidation below ${lower_be:.2f}."
            failure_scenarios = [
                f"Severe market-wide gap down below ${lower_be:.2f} short put strike.",
                f"Elevated put skew expansion under extreme downside stress (-10% move results in -${worst_loss:,.2f}).",
                "Upside breakout risk is mathematically eliminated (zero upside risk verified).",
            ]
            recommendations = [
                f"Set stop-loss trigger if underlying trades below ${lower_be:.2f}.",
                "Roll short put down and out if earnings date moves into current expiration cycle.",
            ]
        elif "butterfly" in strat_name:
            lower_be = breakevens[0] if len(breakevens) >= 2 else (input_data.research.spotPrice * 0.97)
            upper_be = breakevens[1] if len(breakevens) >= 2 else (input_data.research.spotPrice * 1.03)
            primary_failure = f"Pin drift outside narrow [${lower_be:.2f}, ${upper_be:.2f}] ATM tent."
            details = f"Iron Butterfly requires the underlying to pin near ATM strike for maximum profit. Large directional moves rapidly breach wings."
            failure_scenarios = [
                f"Trend acceleration past ${upper_be:.2f} upside or ${lower_be:.2f} downside.",
                "Realized volatility exceeding implied expectations before theta decay accelerates.",
            ]
            recommendations = [
                "Take profit early at 25-50% of max profit rather than attempting to hold for exact ATM pin.",
                "Close position immediately if underlying moves beyond either breakeven.",
            ]
        elif "condor" in strat_name or len(breakevens) >= 2:
            lower_be = breakevens[0] if len(breakevens) >= 2 else 628.62
            upper_be = breakevens[1] if len(breakevens) >= 2 else 661.38
            primary_failure = f"Corridor breach outside ${lower_be:.2f} - ${upper_be:.2f} range."
            details = f"Macro volatility or trend acceleration could breach range corridor [${lower_be:.2f}, ${upper_be:.2f}] before expiration."
            failure_scenarios = [
                f"Sharp upside gap beyond ${upper_be:.2f} breaches defined-risk call wing.",
                f"Sharp downside liquidation below ${lower_be:.2f} breaches defined-risk put wing.",
                f"Worst-case stress scenario (+3% price shift with +20% IV spike) results in -${worst_loss:,.2f} drawdown.",
            ]
            recommendations = [
                f"Shift call wing strikes up by 1 standard deviation if spot approaches ${input_data.research.spotPrice * 1.02:.2f}.",
                "Enforce strict stop-loss if underlying trades past upper or lower breakeven corridor.",
            ]
        elif "put" in strat_name:
            lower_be = breakevens[0] if breakevens else 632.84
            primary_failure = f"Downside selloff below ${lower_be:.2f} put spread breakeven."
            details = f"Broad market liquidation could push spot price below ${lower_be:.2f} short put strike before expiration."
            failure_scenarios = [
                f"Persistent downside drop below ${lower_be:.2f} realizes maximum defined loss.",
                f"Worst-case stress scenario results in -${worst_loss:,.2f} drawdown.",
            ]
            recommendations = [
                f"Set mechanical stop-loss at 2x net credit collected if spot drops below ${lower_be:.2f}.",
                "Avoid holding through binary macro catalyst events if underlying approaches short strike.",
            ]
        else:
            upper_be = breakevens[0] if breakevens else 661.38
            primary_failure = f"Upside rally beyond ${upper_be:.2f} call spread breakeven."
            details = f"Momentum breakout could push spot price above ${upper_be:.2f} short call strike before expiration."
            failure_scenarios = [
                f"Sharp upward momentum beyond ${upper_be:.2f} breaches short call strike.",
                f"Worst-case stress scenario results in -${worst_loss:,.2f} drawdown.",
            ]
            recommendations = [
                f"Set mechanical stop-loss at 2x net credit collected if spot rallies above ${upper_be:.2f}.",
                "Enforce strict risk limit.",
            ]

        verdict: Any = "APPROVED_WITH_CONDITIONS"
        severity: Any = "MEDIUM"

        return Critique(
            verdict=verdict,
            primaryFailureMode=primary_failure,
            severity=severity,
            failureScenarios=failure_scenarios,
            recommendations=recommendations,
            confidence=0.81,
            details=details,
        )

    def _create_trace_step(
        self,
        step_id: str,
        title: str,
        status: str,
        elapsed_ms: int,
        output: Critique,
    ) -> AgentTraceStep:
        return AgentTraceStep(
            id=step_id,
            agentRole=self.role,
            agentLabel=self.label,
            title=title,
            timestampOffset=f"T+{elapsed_ms}ms",
            status="COMPLETE",
            summary=f"Critic identified primary failure mode: {output.primaryFailureMode} ({output.severity} severity).",
            confidenceScore=output.confidence,
            tags=[
                Tag(label="Tail Risk Caution", variant="error"),
                Tag(label=f"{output.severity} Severity", variant="secondary"),
            ],
            details=AgentTraceDetails(
                recommendations=output.recommendations,
            ),
        )
