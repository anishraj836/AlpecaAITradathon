"""
VOLTRON Alpaca Multi-Leg (MLEG) Order Compiler
Translates DecisionPacket domain models into strictly validated Alpaca MLEG order structures
compatible with both direct Alpaca REST/SDK execution and official Alpaca MCP tools.
"""

from typing import Dict, Any, List, Optional
from app.config import settings
from app.domain.models import (
    DecisionPacket,
    MlegOrderPayload,
    MlegOrderLegPayload,
)

class MlegOrderCompiler:
    """
    Deterministic compiler for Alpaca Multi-Leg (MLEG) options orders.
    """

    @classmethod
    def compile_order_payload(
        cls,
        decision: DecisionPacket,
        target_qty: int = 1,
    ) -> MlegOrderPayload:
        """
        Compile an MlegOrderPayload from a validated DecisionPacket.
        Preserves the exact field mapping and validation logic proven in trading.py.
        """
        strategy = decision.strategy
        if not strategy or not strategy.legs:
            raise ValueError(f"Execution Error: Decision {decision.id} has no options legs.")

        # Safety Gate: Paper Trading Check
        if not settings.ALPACA_PAPER:
            raise ValueError("Safety Gate Violation: Live trading is disabled in VOLTRON configuration.")

        underlying = decision.underlying.upper()
        if strategy.underlying.upper() != underlying:
            raise ValueError(
                f"Validation Error: Strategy underlying '{strategy.underlying}' does not match decision underlying '{underlying}'."
            )

        if len(strategy.legs) < 2:
            raise ValueError(f"Validation Error: MLEG execution requires >= 2 legs, got {len(strategy.legs)}.")

        compiled_legs: List[MlegOrderLegPayload] = []

        for idx, leg in enumerate(strategy.legs):
            if not leg.symbol:
                raise ValueError(f"Validation Error: Leg #{idx+1} is missing a contract symbol.")

            if not leg.symbol.upper().startswith(underlying):
                raise ValueError(
                    f"Validation Error: Leg #{idx+1} contract symbol '{leg.symbol}' does not match underlying '{underlying}'."
                )

            side_lower = leg.side.lower()
            if side_lower not in ["buy", "sell"]:
                raise ValueError(f"Validation Error: Invalid side '{leg.side}' on leg {leg.symbol}.")

            ratio = leg.ratio if leg.ratio and leg.ratio > 0 else 1
            pos_intent = "buy_to_open" if side_lower == "buy" else "sell_to_open"

            compiled_legs.append(
                MlegOrderLegPayload(
                    symbol=leg.symbol,
                    ratio_qty=ratio * target_qty,
                    side=side_lower,  # type: ignore
                    position_intent=pos_intent,  # type: ignore
                )
            )

        limit_price = round(abs(strategy.netCreditOrDebit), 2) if strategy.netCreditOrDebit else 1.38
        if limit_price <= 0:
            limit_price = 0.05

        return MlegOrderPayload(
            symbol=underlying,
            orderType="limit",
            timeInForce="day",
            limitPrice=limit_price,
            legs=compiled_legs,
        )

    @classmethod
    def compile_and_validate(
        cls,
        decision: DecisionPacket,
        target_qty: int = 1,
    ) -> MlegOrderPayload:
        """Alias for compile_order_payload for backward compatibility with execution tests."""
        return cls.compile_order_payload(decision, target_qty=target_qty)

    @classmethod
    def to_alpaca_multileg_dict(
        cls,
        payload: MlegOrderPayload,
        client_order_id: Optional[str] = None,
        qty: int = 1,
    ) -> Dict[str, Any]:
        """
        Convert MlegOrderPayload into the exact dictionary shape expected by
        Alpaca's MLEG order API and the alpaca_place_multileg_order MCP tool.
        """
        legs_data = [
            {
                "symbol": leg.symbol,
                "ratio_qty": str(leg.ratio_qty),
                "side": leg.side.lower(),
                "position_intent": leg.position_intent,
            }
            for leg in payload.legs
        ]

        limit_price = payload.limitPrice if payload.limitPrice is not None else 1.38
        cid = client_order_id or f"cl-{payload.symbol}"

        return {
            "qty": str(qty),
            "type": payload.orderType.lower() if payload.orderType else "limit",
            "time_in_force": payload.timeInForce.lower() if payload.timeInForce else "day",
            "limit_price": str(limit_price),
            "order_class": "mleg",
            "client_order_id": cid,
            "legs": legs_data,
        }
