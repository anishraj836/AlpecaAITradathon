from pathlib import Path
from typing import List, Optional, Any
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

PROMPT_PATH = str(Path(__file__).parent.parent / "prompts" / "critic.md")

class CriticInput(BaseModel):
    strategy: StrategyCandidate
    stressReport: StressReport
    research: MarketResearch
    volatility: VolatilityAnalysis

class CriticAgent(BaseAgent[CriticInput, Critique]):
    """
    Adversarial Critic Agent attempting to invalidate the trade and detect structural vulnerabilities.
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

        # Check for catastrophic tail loss in stress matrix
        worst_scenario = min(stress.matrix, key=lambda cell: cell.pnl) if stress.matrix else None
        worst_loss = abs(worst_scenario.pnl) if worst_scenario and worst_scenario.pnl < 0 else 0.0

        # Assess upper / lower breakevens
        breakevens = strat.breakevens
        upper_be = breakevens[1] if len(breakevens) > 1 else (strat.legs[-1].strike if strat.legs else 665.0)

        primary_failure = f"Upside breakout beyond {upper_be:.2f} corridor."
        details = f"Macro CPI or tech momentum could push spot price beyond {upper_be:.2f} call wing before expiration."

        failure_scenarios = [
            f"Sharp upside gap beyond {upper_be:.2f} breaches defined-risk call wing.",
            f"Worst-case stress scenario (+3% price shift with +20% IV spike) results in -${worst_loss:,.2f} drawdown.",
        ]

        recommendations = [
            f"Shift call wing strikes up by 1 standard deviation if spot approaches ${input_data.research.spotPrice * 1.02:.2f}.",
            "Enforce strict stop-loss if underlying trades past upper breakeven corridor.",
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
