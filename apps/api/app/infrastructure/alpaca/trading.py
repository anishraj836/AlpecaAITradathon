import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from app.config import settings
from app.domain.models import DecisionPacket, MlegOrderPayload, OrderResult
from app.infrastructure.alpaca.normalizer import AlpacaNormalizer

logger = logging.getLogger("AlpacaTradingService")

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AlpacaTradingService:
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.client = client
        self.headers = {
            "APCA-API-KEY-ID": settings.ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": settings.ALPACA_SECRET_KEY,
            "Content-Type": "application/json",
        }

    async def place_multileg_order(
        self,
        decision: DecisionPacket,
        order_payload: Optional[MlegOrderPayload] = None,
    ) -> OrderResult:
        # Strict Safety Gate: Enforce Paper Environment
        if not settings.ALPACA_PAPER:
            raise ValueError("Safety Gate Violation: Live trading is disabled in VOLTRON configuration.")

        # Construct MLEG Order Payload
        legs_data = []
        if order_payload and order_payload.legs:
            for leg in order_payload.legs:
                legs_data.append({
                    "symbol": leg.symbol,
                    "ratio_qty": str(leg.ratio_qty),
                    "side": leg.side.lower(),
                    "position_intent": leg.position_intent,
                })
        elif decision.strategy and decision.strategy.legs:
            for leg in decision.strategy.legs:
                pos_intent = "buy_to_open" if leg.side.lower() == "buy" else "sell_to_open"
                legs_data.append({
                    "symbol": leg.symbol,
                    "ratio_qty": str(leg.ratio or 1),
                    "side": leg.side.lower(),
                    "position_intent": pos_intent,
                })

        limit_price = abs(decision.strategy.netCreditOrDebit) if decision.strategy else 1.38
        if order_payload and order_payload.limitPrice is not None:
            limit_price = order_payload.limitPrice

        alpaca_payload: Dict[str, Any] = {
            "qty": "1",
            "type": "limit",
            "time_in_force": "day",
            "limit_price": str(limit_price),
            "order_class": "mleg",
            "client_order_id": f"cl-{decision.id}",
            "legs": legs_data,
        }

        # Offline / Mock Fallback Execution if dummy credentials configured
        if not settings.ALPACA_API_KEY or "DUMMY" in settings.ALPACA_API_KEY:
            now_dt = _utc_now()
            mock_order_response = {
                "id": f"ALP-ORD-{now_dt.strftime('%H%M%S')}",
                "client_order_id": f"cl-{decision.id}",
                "status": "accepted",
                "symbol": decision.underlying,
                "limit_price": limit_price,
                "qty": "1",
                "filled_avg_price": limit_price,
                "filled_at": now_dt.isoformat() + "Z",
            }
            return AlpacaNormalizer.normalize_order_result(mock_order_response, decision.id)

        # Real Paper Dispatch
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.ALPACA_BASE_URL}/v2/orders",
                headers=self.headers,
                json=alpaca_payload,
                timeout=15.0,
            )
            if resp.status_code >= 400:
                logger.error(f"Alpaca Order Error ({resp.status_code}): {resp.text} | Payload: {alpaca_payload}")
                # Parse rejection payload gracefully
                now_dt = _utc_now()
                return OrderResult(
                    orderId=f"ALP-REJECTED-{now_dt.strftime('%M%S')}",
                    decisionId=decision.id,
                    clientOrderId=f"cl-{decision.id}",
                    status="rejected",
                    filledAt=now_dt.isoformat() + "Z",
                    avgPrice=limit_price,
                    broker="ALPACA_PAPER",
                    rawPayload=alpaca_payload,
                )
            return AlpacaNormalizer.normalize_order_result(resp.json(), decision.id)

    async def get_order(self, order_id: str, decision_id: Optional[str] = None) -> OrderResult:
        if not settings.ALPACA_API_KEY or "DUMMY" in settings.ALPACA_API_KEY:
            dec_id = decision_id or (order_id.replace("ALP-ORD-", "DEC-") if "ALP-ORD-" in order_id else "DEC-SPY-9942")
            mock_order_response = {
                "id": order_id,
                "client_order_id": f"cl-{dec_id}",
                "status": "filled",
                "filled_avg_price": 1.38,
                "filled_qty": 1,
            }
            return AlpacaNormalizer.normalize_order_result(mock_order_response, dec_id)

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.ALPACA_BASE_URL}/v2/orders/{order_id}",
                headers=self.headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            raw_order = resp.json()
            client_order_id = str(raw_order.get("client_order_id", ""))
            extracted_decision_id = client_order_id.replace("cl-", "") if client_order_id.startswith("cl-") else (decision_id or "UNKNOWN")
            return AlpacaNormalizer.normalize_order_result(raw_order, extracted_decision_id)
