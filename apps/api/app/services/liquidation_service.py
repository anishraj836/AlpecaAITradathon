import re
import logging
from datetime import datetime, timezone, date
from typing import List, Optional, Dict, Any
from app.domain.models import PositionInfo, LiquidationEvaluation, LiquidationBatchResult
from app.infrastructure.alpaca.gateway import BrokerGateway
from app.services.learning_service import learning_service

logger = logging.getLogger("LiquidationService")

OCC_PATTERN = re.compile(r"^([A-Z]{1,6})(\d{2})(\d{2})(\d{2})([CP])(\d{8})$")

class LiquidationService:
    """
    VOLTRON Quantitative Autonomous Liquidation Engine:
    Evaluates open stock and options positions against institutional risk rules:
    1. 50% Profit Target Rule: Capture 50% of credit received on short option structures (optimal Sharpe).
    2. 200% Stop Loss Rule: Cut losses when loss exceeds 2x entry premium to contain tail risk.
    3. Expiration Gamma & Pin Risk: Liquidate options with <= 2 DTE to eliminate assignment and weekend gap risk.
    4. Long Wing Surge: Liquidate long options with >= 80% unrealized gain.
    """

    def parse_occ_symbol(self, symbol: str) -> Dict[str, Any]:
        """Parse standard OCC option contract symbol to extract underlying, DTE, strike, and type."""
        match = OCC_PATTERN.match(symbol)
        if not match:
            return {"is_option": False, "underlying": symbol, "dte": None}

        root, yy, mm, dd, cp, strike_raw = match.groups()
        try:
            exp_date = date(2000 + int(yy), int(mm), int(dd))
            today = datetime.now(timezone.utc).date()
            dte = max(0, (exp_date - today).days)
            strike = int(strike_raw) / 1000.0
            return {
                "is_option": True,
                "underlying": root,
                "expiration": exp_date.isoformat(),
                "dte": dte,
                "type": "CALL" if cp == "C" else "PUT",
                "strike": strike,
            }
        except Exception:
            return {"is_option": True, "underlying": root, "dte": None}

    def evaluate_position(self, pos: PositionInfo) -> LiquidationEvaluation:
        """
        Evaluate a single open position against quantitative liquidation rules.
        """
        parsed = self.parse_occ_symbol(pos.symbol)
        is_option = parsed["is_option"]
        dte = parsed.get("dte")
        underlying = parsed["underlying"]

        # Cost basis in dollars
        multiplier = 100.0 if is_option else 1.0
        cost_basis = max(0.01, abs(pos.avgEntryPrice * pos.qty * multiplier))
        pnl_pct = round(pos.unrealizedPl / cost_basis, 4)

        # -------------------------------------------------------------
        # Rule 1: 50% Profit Target (Standard Institutional / Tasty Rule)
        # -------------------------------------------------------------
        if pos.side == "short":
            if pnl_pct >= 0.50:
                return LiquidationEvaluation(
                    symbol=pos.symbol,
                    qty=abs(pos.qty),
                    side=pos.side,
                    avgEntryPrice=pos.avgEntryPrice,
                    currentPrice=pos.currentPrice,
                    unrealizedPl=pos.unrealizedPl,
                    pnlPct=pnl_pct,
                    dte=dte,
                    shouldLiquidate=True,
                    reason="PROFIT_TARGET_50",
                    actionLabel=f"Take Profit (+{pnl_pct*100:.0f}%)",
                    explanation=f"Captured {pnl_pct*100:.1f}% profit target. Theta decay largely harvested. Locking in +${pos.unrealizedPl:.2f}.",
                )
        elif pos.side == "long":
            if pnl_pct >= 0.80:
                return LiquidationEvaluation(
                    symbol=pos.symbol,
                    qty=abs(pos.qty),
                    side=pos.side,
                    avgEntryPrice=pos.avgEntryPrice,
                    currentPrice=pos.currentPrice,
                    unrealizedPl=pos.unrealizedPl,
                    pnlPct=pnl_pct,
                    dte=dte,
                    shouldLiquidate=True,
                    reason="PROFIT_TARGET_LONG",
                    actionLabel=f"Take Profit (+{pnl_pct*100:.0f}%)",
                    explanation=f"Long option gained +{pnl_pct*100:.1f}%. Locking in +${pos.unrealizedPl:.2f} hedge profit.",
                )

        # -------------------------------------------------------------
        # Rule 2: 200% Mechanical Stop Loss (Risk Containment)
        # -------------------------------------------------------------
        if pnl_pct <= -2.00:
            return LiquidationEvaluation(
                symbol=pos.symbol,
                qty=abs(pos.qty),
                side=pos.side,
                avgEntryPrice=pos.avgEntryPrice,
                currentPrice=pos.currentPrice,
                unrealizedPl=pos.unrealizedPl,
                pnlPct=pnl_pct,
                dte=dte,
                shouldLiquidate=True,
                reason="STOP_LOSS_200",
                actionLabel=f"Cut Loss ({pnl_pct*100:.0f}%)",
                explanation=f"Unrealized loss reached {pnl_pct*100:.1f}%. Mechanical stop-loss triggered to protect capital.",
            )

        # -------------------------------------------------------------
        # Rule 3: Expiration Gamma & Pin Risk (DTE <= 2 days)
        # -------------------------------------------------------------
        if is_option and dte is not None and dte <= 2:
            return LiquidationEvaluation(
                symbol=pos.symbol,
                qty=abs(pos.qty),
                side=pos.side,
                avgEntryPrice=pos.avgEntryPrice,
                currentPrice=pos.currentPrice,
                unrealizedPl=pos.unrealizedPl,
                pnlPct=pnl_pct,
                dte=dte,
                shouldLiquidate=True,
                reason="EXPIRATION_PIN_RISK",
                actionLabel=f"Close Risk ({dte}d DTE)",
                explanation=f"Option is {dte} day(s) from expiration. Liquidating to eliminate gamma acceleration and broker pin risk.",
            )

        # Default: Hold position
        return LiquidationEvaluation(
            symbol=pos.symbol,
            qty=abs(pos.qty),
            side=pos.side,
            avgEntryPrice=pos.avgEntryPrice,
            currentPrice=pos.currentPrice,
            unrealizedPl=pos.unrealizedPl,
            pnlPct=pnl_pct,
            dte=dte,
            shouldLiquidate=False,
            reason="HOLD",
            actionLabel="Hold",
            explanation=f"Position within normal risk bounds (PnL: {pnl_pct*100:+.1f}%, DTE: {dte if dte is not None else 'N/A'}).",
        )

    def evaluate_all(self, positions: List[PositionInfo]) -> List[LiquidationEvaluation]:
        """Evaluate a list of positions and return recommendations."""
        return [self.evaluate_position(p) for p in positions]

    async def execute_liquidation(
        self,
        pos: PositionInfo,
        eval_result: LiquidationEvaluation,
        broker: BrokerGateway,
    ) -> Dict[str, Any]:
        """
        Execute liquidation on Alpaca Paper Broker and feed outcome into Learning Engine.
        """
        try:
            logger.info(f"Liquidating position {pos.symbol} (Reason: {eval_result.reason})")
            resp = await broker.close_position(pos.symbol, qty=abs(pos.qty))

            # Infer strategy family for learning engine feedback
            parsed = self.parse_occ_symbol(pos.symbol)
            family = "IRON_CONDOR"
            if "C" in pos.symbol:
                family = "CALL_CREDIT_SPREAD"
            elif "P" in pos.symbol:
                family = "PUT_CREDIT_SPREAD"

            won = eval_result.unrealizedPl >= 0.0
            pnl = eval_result.unrealizedPl
            learning_service.record_outcome(family, won=won, pnl=pnl)

            return {
                "success": True,
                "symbol": pos.symbol,
                "reason": eval_result.reason,
                "explanation": eval_result.explanation,
                "realizedPnl": pnl,
                "brokerResponse": resp,
            }
        except Exception as e:
            logger.error(f"Error liquidating {pos.symbol}: {e}", exc_info=True)
            return {
                "success": False,
                "symbol": pos.symbol,
                "error": str(e),
            }

    async def liquidate_eligible(
        self,
        positions: List[PositionInfo],
        broker: BrokerGateway,
    ) -> LiquidationBatchResult:
        """
        Scan all positions, identify eligible ones, and execute liquidations.
        """
        evaluations = self.evaluate_all(positions)
        liquidated_count = 0
        total_pnl = 0.0

        for pos, ev in zip(positions, evaluations):
            if ev.shouldLiquidate:
                res = await self.execute_liquidation(pos, ev, broker)
                if res.get("success"):
                    liquidated_count += 1
                    total_pnl += ev.unrealizedPl

        return LiquidationBatchResult(
            evaluated=len(positions),
            liquidatedCount=liquidated_count,
            totalRealizedPnl=round(total_pnl, 2),
            evaluations=evaluations,
        )

# Global singleton
liquidation_service = LiquidationService()
