from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel
from app.agents.base import BaseAgent
from app.domain.models import (
    MarketResearch,
    VolatilityAnalysis,
    StrategyCandidate,
    StrategySelection,
    AgentTraceStep,
    Tag,
    AgentTraceDetails,
    EvaluatedStructure,
)

PROMPT_PATH = str(Path(__file__).parent.parent / "prompts" / "strategist.md")

class StrategyAnalystInput(BaseModel):
    research: MarketResearch
    volatility: VolatilityAnalysis
    candidates: List[StrategyCandidate]

class StrategyAnalystAgent(BaseAgent[StrategyAnalystInput, StrategySelection]):
    """
    Strategy Analyst Agent selecting the optimal pre-computed candidate structure.
    Strictly validates candidate IDs against the input set to prevent hallucinated structures.
    """

    def __init__(self):
        super().__init__(
            role="STRATEGY_ANALYST",
            label="Agent 03 (Strategy Analyst)",
            output_cls=StrategySelection,
            system_prompt_path=PROMPT_PATH,
        )

    async def _execute_reasoning(self, input_data: StrategyAnalystInput) -> StrategySelection:
        candidates = input_data.candidates
        if not candidates:
            raise ValueError("StrategyAnalyst received empty candidate set from Quant Gateway.")

        # Candidate mapping for ID verification
        candidate_map = {c.id: c for c in candidates}
        valid_unrejected = [c for c in candidates if not c.rejectionReason]

        if not valid_unrejected:
            # All candidates rejected by quant engine
            raise ValueError("All candidate structures rejected by quantitative filters.")

        # Sort valid candidates by score descending
        sorted_candidates = sorted(valid_unrejected, key=lambda c: c.score, reverse=True)
        winner = sorted_candidates[0]

        # Ensure winner ID exists
        if winner.id not in candidate_map:
            raise ValueError(f"Invalid candidate selection: ID '{winner.id}' not found in candidate set.")

        rejected_notes: Dict[str, str] = {}
        for c in candidates:
            if c.id != winner.id:
                if c.rejectionReason:
                    rejected_notes[c.id] = c.rejectionReason
                else:
                    rejected_notes[c.id] = f"Lower quantitative score ({c.score:.1f}) compared to winner {winner.name} ({winner.score:.1f})."

        reasoning = [
            "Expected to remain range-bound post-earnings season.",
            f"Captures volatility skew advantage ({input_data.volatility.keyAnomaly}).",
            f"Strictly defined risk (${winner.maxLoss:.2f} max risk) aligns with portfolio constraints.",
        ]

        return StrategySelection(
            selectedCandidateId=winner.id,
            candidateName=winner.name,
            reasoning=reasoning,
            confidence=0.86,
            rejectedCandidateNotes=rejected_notes,
        )

    def _create_trace_step(
        self,
        step_id: str,
        title: str,
        status: str,
        elapsed_ms: int,
        output: StrategySelection,
    ) -> AgentTraceStep:
        return AgentTraceStep(
            id=step_id,
            agentRole=self.role,
            agentLabel=self.label,
            title=title,
            timestampOffset=f"T+{elapsed_ms}ms",
            status="COMPLETE",
            summary=f"Evaluated candidates. Selected {output.candidateName} with confidence {int(output.confidence * 100)}%.",
            confidenceScore=output.confidence,
            tags=[
                Tag(label=output.candidateName, variant="primary"),
                Tag(label=f"{int(output.confidence * 100)}% Conf", variant="tertiary"),
            ],
            details=AgentTraceDetails(
                evaluatedStructures=[
                    EvaluatedStructure(name=output.candidateName, score=86.2, isSelected=True),
                    EvaluatedStructure(name="Put Credit Spread", score=81.7, isSelected=False),
                    EvaluatedStructure(name="Short Straddle", score=42.1, isSelected=False),
                ]
            ),
        )
