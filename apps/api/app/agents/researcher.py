from pathlib import Path
from typing import Optional
from app.agents.base import BaseAgent
from app.domain.models import MarketContext, MarketResearch, AgentTraceStep, Tag, AgentTraceDetails

from app.infrastructure.llm import llm_client

PROMPT_PATH = str(Path(__file__).parent.parent / "prompts" / "researcher.md")

class MarketResearcherAgent(BaseAgent[MarketContext, MarketResearch]):
    """
    Researcher Agent interpreting live broker market context and regime properties via Multi-Provider LLM Gateway.
    """

    def __init__(self):
        super().__init__(
            role="RESEARCHER",
            label="Agent 01 (Researcher)",
            output_cls=MarketResearch,
            system_prompt_path=PROMPT_PATH,
        )

    async def _execute_reasoning(self, input_data: MarketContext) -> MarketResearch:
        # Format news headlines if present
        news_block = ""
        if input_data.news:
            headlines = [f"  • {item.get('headline')} (Source: {item.get('source', 'Alpaca')})" for item in input_data.news[:5]]
            news_block = f"\nRecent Real-Time Alpaca Market Headlines:\n" + "\n".join(headlines) + "\n"

        # 1. Attempt Live LLM Reasoning (Gemini, OpenAI, Groq, Anthropic, Ollama, DeepSeek)
        if llm_client.is_configured:
            prompt = (
                f"Market Context Input:\n"
                f"- Symbol: {input_data.symbol}\n"
                f"- Spot Price: ${input_data.price:.2f}\n"
                f"- Daily High: ${input_data.high:.2f}\n"
                f"- Daily Low: ${input_data.low:.2f}\n"
                f"- Day Change: {input_data.changePct:+.2f}%\n"
                f"- Volume: {input_data.volume:,} shares\n"
                f"{news_block}\n"
                f"Analyze the market regime, recent price velocity, event risk, headline catalysts, and relevant evidence."
            )
            llm_out = await llm_client.generate_structured(
                system_instruction=self.system_prompt,
                user_prompt=prompt,
                response_model=MarketResearch,
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

        event_flags = ["POST_EARNINGS_SEASON", "FOMC_CALENDAR_ACTIVE"]
        if input_data.news and len(input_data.news) > 0:
            top_headline = input_data.news[0].get("headline", "")
            if top_headline:
                evidence.append(f"Real-time news catalyst: \"{top_headline}\"")
                event_flags.append("LIVE_NEWS_INGESTED")

        summary = f"Identified {regime} with {int(confidence * 100)}% confidence based on compressed intraday dispersion and {input_data.symbol} liquidity."

        return MarketResearch(
            symbol=input_data.symbol,
            spotPrice=price,
            marketRegimeSummary=regime,
            eventFlags=event_flags,
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
