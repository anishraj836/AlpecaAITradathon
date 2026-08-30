from pathlib import Path
from app.agents.base import BaseAgent
from app.domain.models import VolatilitySurface, VolatilityAnalysis
from app.infrastructure.gemini.client import gemini_client

PROMPT_PATH = str(Path(__file__).parent.parent / "prompts" / "volatility.md")

class VolatilityAnalystAgent(BaseAgent[VolatilitySurface, VolatilityAnalysis]):
    """
    AI Agent 02: Volatility Analyst (powered by Gemini LLM).
    Interprets skew asymmetry, term structure slope, IV percentile, and statistical anomalies.
    """

    def __init__(self):
        super().__init__(
            role="VOLATILITY_ANALYST",
            label="Agent 02 (Volatility Analyst)",
            output_cls=VolatilityAnalysis,
            system_prompt_path=PROMPT_PATH,
        )

    async def _execute_reasoning(self, input_data: VolatilitySurface) -> VolatilityAnalysis:
        # 1. Attempt Live Gemini LLM Reasoning
        if gemini_client.is_configured:
            prompt = (
                f"Volatility Surface Metrics for {input_data.underlying}:\n"
                f"- ATM IV: {input_data.skewSnapshot.atmIV:.1f}%\n"
                f"- 25Δ Put IV: {input_data.skewSnapshot.put25DeltaIV:.1f}%\n"
                f"- 25Δ Call IV: {input_data.skewSnapshot.call25DeltaIV:.1f}%\n"
                f"- Put/Call Skew Ratio: {input_data.skewSnapshot.skewRatio:.2f}x\n"
                f"- Detected Anomalies: {[a.description for a in input_data.anomalies]}\n\n"
                f"Interpret the skew asymmetry, term structure slope, and statistical vol anomalies."
            )
            gemini_out = await gemini_client.generate_structured(
                system_instruction=self.system_prompt,
                user_prompt=prompt,
                response_model=VolatilityAnalysis,
            )
            if gemini_out:
                return gemini_out

        # 2. Deterministic Fallback Engine
        skew_ratio = input_data.skewSnapshot.skewRatio
        atm_iv = input_data.skewSnapshot.atmIV
        put_iv = input_data.skewSnapshot.put25DeltaIV
        call_iv = input_data.skewSnapshot.call25DeltaIV

        is_put_skew_elevated = skew_ratio >= 1.15
        skew_interp = (
            f"25Δ Put IV ({put_iv:.1f}%) is trading at {skew_ratio:.2f}x above 25Δ Call IV ({call_iv:.1f}%), indicating elevated downside put skew."
            if is_put_skew_elevated
            else f"25Δ Put IV ({put_iv:.1f}%) vs 25Δ Call IV ({call_iv:.1f}%) indicates balanced skew."
        )

        anom_descriptions = [a.description for a in input_data.anomalies] if input_data.anomalies else ["No statistical skew anomalies detected."]
        
        if input_data.termStructure and len(input_data.termStructure) > 1:
            term_interp = (
                f"Term structure shows front-end {input_data.termStructure[0].label} IV ({input_data.termStructure[0].iv:.1f}%) "
                f"vs back-end {input_data.termStructure[-1].label} IV ({input_data.termStructure[-1].iv:.1f}%), "
                f"indicating {'heightened front-month hedging demand' if input_data.termStructure[0].iv > input_data.termStructure[-1].iv else 'normal contango term structure'}."
            )
        elif input_data.termStructure:
            term_interp = f"Single term structure node available at {input_data.termStructure[0].iv:.1f}% IV."
        else:
            term_interp = "Term structure data unavailable for underlying."

        summary = (
            f"25D Put IV is trading at {put_iv:.1f}% vs 25D Call IV at {call_iv:.1f}% (Skew Ratio: {skew_ratio:.2f}x). "
            f"ATM IV is {atm_iv:.1f}%. Skew is classified as PUT_SKEW_ELEVATED. "
            f"{term_interp}"
        )

        return VolatilityAnalysis(
            symbol=input_data.underlying,
            keyAnomaly=input_data.anomalies[0].name if input_data.anomalies else "NORMAL_SURFACE",
            skewInterpretation=skew_interp,
            termStructureInterpretation=term_interp,
            confidence=0.88 if is_put_skew_elevated else 0.75,
            evidence=anom_descriptions,
            caveats=["IV smile subject to intraday macro event compression"],
            summary=summary,
        )
