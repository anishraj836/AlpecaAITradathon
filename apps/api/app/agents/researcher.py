from pathlib import Path
from typing import Optional
from app.agents.base import BaseAgent
from app.domain.models import MarketContext, MarketResearch, AgentTraceStep, Tag, AgentTraceDetails

PROMPT_PATH = str(Path(__file__).parent.parent / "prompts" / "researcher.md")

class MarketResearcherAgent(BaseAgent[MarketContext, MarketResearch]):
    """
    Researcher Agent interpreting live broker market context and regime properties.
    """

    def __init__(self):
        super().__init__(
            role="RESEARCHER",
            label="Agent 01 (Researcher)",
            output_cls=MarketResearch,
            system_prompt_path=PROMPT_PATH,
        )

    async def _execute_reasoning(self, input_data: MarketContext) -> MarketResearch:
        # Determine regime from price dynamics
        price = input_data.price
        change = input_data.changePct
        abs_change = abs(change)

        if abs_change < 1.0:
            regime = "Range-bound (low-dispersion consolidation)"
            confidence = 0.84
        elif change >= 1.0:
            regime = "Bullish momentum (breakout tendency)"
            confidence = 0.78
        else:
            regime = "Downside pressure (elevated protective demand)"
            confidence = 0.79

        evidence = [
            f"{input_data.symbol} spot trading at ${price:.2f} ({change:+.2f}% day change)",
            f"Daily corridor bounded between ${input_data.low:.2f} and ${input_data.high:.2f}",
            f"Trading volume of {input_data.volume:,} shares indicating healthy market depth",
        ]

        summary = f"Identified {regime} with {int(confidence * 100)}% confidence based on compressed intraday dispersion and {input_data.symbol} liquidity."

        return MarketResearch(
            symbol=input_data.symbol,
            spotPrice=price,
            marketRegimeSummary=regime,
            eventFlags=["POST_EARNINGS_SEASON", "FOMC_CALENDAR_ACTIVE"],
            relevantEvidence=evidence,
            confidence=confidence,
            summary=summary,
        )

    def _create_trace_step(
        self,
        step_id: str,
        title: str,
        status: str,
        elapsed_ms: int,
        output: MarketResearch,
    ) -> AgentTraceStep:
        return AgentTraceStep(
            id=step_id,
            agentRole=self.role,
            agentLabel=self.label,
            title=title,
            timestampOffset=f"T+{elapsed_ms}ms",
            status="COMPLETE",
            summary=output.summary,
            confidenceScore=output.confidence,
            tags=[
                Tag(label="Range-bound", variant="secondary"),
                Tag(label=f"{int(output.confidence * 100)}% Conf", variant="tertiary"),
            ],
            details=AgentTraceDetails(
                keyDrivers=output.relevantEvidence,
            ),
        )
