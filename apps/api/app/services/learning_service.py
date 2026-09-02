import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.repositories.decisions import DecisionRepository
from strategies import update_bandit_feedback, get_bandit_metrics, _BANDIT_PRIORS

logger = logging.getLogger("LearningEngineService")

class LearningEngineService:
    """
    VOLTRON Quantitative Learning Engine:
    1. Ingests historical decision and execution records from SQLite database.
    2. Builds an Empirical Experience & Reflexion Buffer for LLM Agents (Strategy Analyst & Risk Critic).
    3. Maintains Bayesian Thompson Sampling Multi-Armed Bandit weights for candidate strategy scoring.
    4. Tracks loss post-mortems to dynamically penalize vulnerable setups.
    """

    def __init__(self):
        self._cache_memory: Optional[Dict[str, Any]] = None

    async def get_learning_memory(self, session: AsyncSession, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Builds live experiential memory buffer from persisted decisions and broker executions.
        """
        try:
            repo = DecisionRepository(session)
            recent_decisions = await repo.list_recent(limit=50)

            total_evaluated = len(recent_decisions)
            approved_count = 0
            rejected_count = 0
            strategy_counts: Dict[str, Dict[str, int]] = {
                "IRON_CONDOR": {"count": 0, "approved": 0},
                "JADE_LIZARD": {"count": 0, "approved": 0},
                "IRON_BUTTERFLY": {"count": 0, "approved": 0},
                "PUT_CREDIT_SPREAD": {"count": 0, "approved": 0},
                "CALL_CREDIT_SPREAD": {"count": 0, "approved": 0},
            }
            loss_post_mortems: List[str] = []

            for d in recent_decisions:
                p_json = d.packet_json or {}
                status = p_json.get("status", d.status)
                strat = p_json.get("strategy", {})
                strat_name = strat.get("name", "").upper()

                family = "IRON_CONDOR"
                if "LIZARD" in strat_name:
                    family = "JADE_LIZARD"
                elif "BUTTERFLY" in strat_name:
                    family = "IRON_BUTTERFLY"
                elif "PUT" in strat_name:
                    family = "PUT_CREDIT_SPREAD"
                elif "CALL" in strat_name:
                    family = "CALL_CREDIT_SPREAD"

                if family in strategy_counts:
                    strategy_counts[family]["count"] += 1

                if status == "APPROVED":
                    approved_count += 1
                    if family in strategy_counts:
                        strategy_counts[family]["approved"] += 1
                elif status == "REJECTED":
                    rejected_count += 1
                    critic_notes = p_json.get("criticAnalysis", {})
                    if critic_notes and isinstance(critic_notes, dict):
                        fail_mode = critic_notes.get("primaryFailureMode")
                        if fail_mode and fail_mode not in loss_post_mortems:
                            loss_post_mortems.append(f"{strat.get('underlying', symbol)}: {fail_mode}")

            bandit_stats: Dict[str, Any] = {}
            for fam in strategy_counts.keys():
                bandit_stats[fam] = get_bandit_metrics(fam)

            prompt_lines = [
                f"- Total Historical Decisions Evaluated: {total_evaluated} ({approved_count} Approved, {rejected_count} Rejected)",
                "- Empirical Bayesian Bandit Strategy Performance:",
            ]
            for fam, stats in bandit_stats.items():
                win_pct = stats["expectedWinRate"] * 100.0
                mult = stats["banditMultiplier"]
                prompt_lines.append(f"  * {fam}: Posterior Win Rate {win_pct:.1f}% | Bandit Multiplier {mult:.2f}x (Prior sample size: {stats['sampleSize']})")

            if loss_post_mortems:
                prompt_lines.append("- Critical Failure Modes to Avoid:")
                for pm in loss_post_mortems[:4]:
                    prompt_lines.append(f"  * {pm}")
            else:
                prompt_lines.append("- Critical Failure Modes: None recorded in recent window; maintain strict defined-risk invariant.")

            learning_summary = "\n".join(prompt_lines)

            memory = {
                "totalEvaluated": total_evaluated,
                "approvedCount": approved_count,
                "rejectedCount": rejected_count,
                "strategyCounts": strategy_counts,
                "banditStats": bandit_stats,
                "lossPostMortems": loss_post_mortems,
                "promptSummary": learning_summary,
            }
            self._cache_memory = memory
            return memory

        except Exception as e:
            logger.error(f"Error computing learning memory: {e}", exc_info=True)
            return {
                "totalEvaluated": 0,
                "approvedCount": 0,
                "rejectedCount": 0,
                "strategyCounts": {},
                "banditStats": {},
                "lossPostMortems": [],
                "promptSummary": "Learning Engine active in baseline cold-start state. Respect strict delta-neutral and defined-risk constraints.",
            }

    def record_outcome(self, strategy_family: str, won: bool, pnl: float = 0.0):
        """
        Feeds live trade result into Bayesian Bandit to update posterior win probabilities.
        """
        weight = 1.0 + min(1.0, abs(pnl) / 500.0) if pnl != 0.0 else 1.0
        update_bandit_feedback(strategy_family, won=won, weight=weight)
        logger.info(f"Learned trade feedback: {strategy_family} (won={won}, pnl=${pnl:,.2f}). Bandit updated.")

# Global singleton
learning_service = LearningEngineService()
