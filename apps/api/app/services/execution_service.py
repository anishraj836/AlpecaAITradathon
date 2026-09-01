import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.domain.models import (
    DecisionPacket,
    StrategyCandidate,
    OptionLeg,
    MlegOrderPayload,
    MlegOrderLegPayload,
    OrderResult,
    DecisionStatus,
)
from app.infrastructure.alpaca.gateway import BrokerGateway
from app.infrastructure.database.repositories.decisions import DecisionRepository
from app.infrastructure.database.repositories.orders import OrderRepository
from app.infrastructure.database.models import OrderModel

logger = logging.getLogger("VoltronExecutionService")

# Process-level decision locks to prevent concurrent approval race conditions
_decision_locks: Dict[str, asyncio.Lock] = {}
_locks_mutex = asyncio.Lock()

async def _get_decision_lock(decision_id: str) -> asyncio.Lock:
    async with _locks_mutex:
        if decision_id not in _decision_locks:
            _decision_locks[decision_id] = asyncio.Lock()
        return _decision_locks[decision_id]

class MlegOrderCompiler:
    """
    Deterministic Multi-Leg (MLEG) Order Compiler & Safety Validator.
    Converts a validated StrategyCandidate into a strictly compliant Alpaca MLEG order payload.
    """

    @classmethod
    def compile_and_validate(
        cls,
        decision: DecisionPacket,
        target_qty: int = 1,
    ) -> MlegOrderPayload:
        strategy = decision.strategy
        if not strategy or not strategy.legs:
            raise ValueError(f"Execution Error: Decision {decision.id} has no options legs.")

        # 1. Enforce Paper Safety Gate
        if not settings.ALPACA_PAPER:
            raise ValueError("CRITICAL SAFETY VIOLATION: Live trading attempted. VOLTRON execution is hard-locked to PAPER.")

        # 2. Validate Underlying Consistency
        underlying = decision.underlying.upper()
        if strategy.underlying.upper() != underlying:
            raise ValueError(
                f"Validation Error: Strategy underlying '{strategy.underlying}' does not match decision underlying '{underlying}'."
            )

        # 3. Validate Leg Count (Defined risk multi-leg requires at least 2 legs)
        if len(strategy.legs) < 2:
            raise ValueError(f"Validation Error: MLEG execution requires >= 2 legs, got {len(strategy.legs)}.")

        compiled_legs: List[MlegOrderLegPayload] = []

        for idx, leg in enumerate(strategy.legs):
            # Check contract symbol format
            if not leg.symbol:
                raise ValueError(f"Validation Error: Leg #{idx+1} is missing a contract symbol.")

            if not leg.symbol.upper().startswith(underlying):
                raise ValueError(
                    f"Validation Error: Leg #{idx+1} contract symbol '{leg.symbol}' does not match underlying '{underlying}'."
                )

            # Check ratio
            ratio = leg.ratio if leg.ratio and leg.ratio > 0 else 1

            # Determine position intent
            side_lower = leg.side.lower()
            if side_lower not in ["buy", "sell"]:
                raise ValueError(f"Validation Error: Invalid side '{leg.side}' on leg {leg.symbol}.")

            position_intent = "buy_to_open" if side_lower == "buy" else "sell_to_open"

            compiled_legs.append(
                MlegOrderLegPayload(
                    symbol=leg.symbol,
                    ratio_qty=ratio * target_qty,
                    side=side_lower, # type: ignore
                    position_intent=position_intent, # type: ignore
                )
            )

        # 4. Determine Limit Price
        limit_price = round(abs(strategy.netCreditOrDebit), 2)
        if limit_price <= 0:
            limit_price = 0.05  # minimum credit/debit threshold

        return MlegOrderPayload(
            symbol=underlying,
            orderType="limit",
            timeInForce="day",
            limitPrice=limit_price,
            legs=compiled_legs,
        )

class ExecutionService:
    """
    Central Execution Pipeline Service.
    Enforces strict lifecycle state machines, concurrency locks, idempotency,
    deterministic risk re-validation, order compilation, broker dispatch, and database persistence.
    """

    def __init__(self, session: AsyncSession, broker_gateway: BrokerGateway):
        self.session = session
        self.broker = broker_gateway
        self.dec_repo = DecisionRepository(session)
        self.order_repo = OrderRepository(session)

    async def approve_and_execute(self, decision_id: str) -> OrderResult:
        lock = await _get_decision_lock(decision_id)
        async with lock:
            # Step 1: Retrieve stored DecisionPacket from DB
            db_model = await self.dec_repo.get_by_id(decision_id)
            if not db_model:
                raise ValueError(f"Decision '{decision_id}' not found.")

            packet = DecisionPacket.model_validate(db_model.packet_json)

            # Step 2: Idempotency Check (Prevent duplicate execution)
            client_order_id = f"cl-{decision_id}"
            existing_order = await self.order_repo.get_order_by_client_id(client_order_id)
            if existing_order or packet.status in ["APPROVED", "EXECUTED"]:
                logger.warning(f"[{decision_id}] Duplicate approval attempt. Returning existing order record.")
                if existing_order:
                    return OrderResult(
                        orderId=existing_order.id,
                        decisionId=decision_id,
                        clientOrderId=existing_order.client_order_id,
                        status=existing_order.status, # type: ignore
                        avgPrice=existing_order.avg_price,
                        qty=existing_order.qty,
                        broker="ALPACA_PAPER",
                        rawResponse=existing_order.raw_payload,
                    )
                else:
                    return OrderResult(
                        orderId=f"ALP-ORD-{decision_id}",
                        decisionId=decision_id,
                        clientOrderId=client_order_id,
                        status="filled",
                        avgPrice=packet.strategy.netCreditOrDebit,
                        qty=1,
                        broker="ALPACA_PAPER",
                    )

            # Step 3: Lifecycle State Machine Validation
            if packet.status in ["REJECTED", "FAILED", "NO_TRADE"]:
                raise ValueError(
                    f"Lifecycle Gate Rejected: Decision '{decision_id}' is in terminal status '{packet.status}' and cannot be approved."
                )

            if packet.status != "AWAITING_APPROVAL":
                raise ValueError(
                    f"Lifecycle Gate Rejected: Decision '{decision_id}' is in status '{packet.status}' (expected AWAITING_APPROVAL)."
                )

            # Step 4: Re-validate Deterministic Risk Compiler Conditions
            if not packet.riskCompilerResult.isApproved:
                raise ValueError(
                    f"Deterministic Risk Compiler Violation: Decision '{decision_id}' failed safety checks and cannot be approved."
                )

            # Step 5: Compile & Validate MLEG Order Payload
            order_payload = MlegOrderCompiler.compile_and_validate(packet)
            packet.mlegOrderPayload = order_payload

            # Step 6: Dispatch Order to Broker Gateway (Paper Environment)
            order_result = await self.broker.place_multileg_order(packet, order_payload)

            # Step 7: Persist Order to DB with IntegrityError Safeguard
            try:
                order_model = OrderModel(
                    id=order_result.orderId,
                    decision_id=decision_id,
                    client_order_id=client_order_id,
                    broker_order_id=order_result.orderId,
                    symbol=packet.underlying,
                    order_type="limit",
                    status=order_result.status,
                    avg_price=order_result.avgPrice,
                    qty=order_result.qty,
                    raw_payload=order_result.rawResponse,
                )
                await self.order_repo.save_order(order_model)

                # Step 8: Update Decision Status based on real broker outcome
                if order_result.status in ("accepted", "filled", "new", "partially_filled", "held"):
                    packet.status = "APPROVED"
                    logger.info(f"[{decision_id}] Successfully approved and executed paper order: {order_result.orderId}")
                else:
                    packet.status = "REJECTED"
                    logger.warning(f"[{decision_id}] Broker rejected order: {order_result.orderId}. Status: {order_result.status}")

                await self.dec_repo.save(packet)
                await self.session.commit()
            except IntegrityError:
                await self.session.rollback()
                existing_order = await self.order_repo.get_order_by_client_id(client_order_id)
                if existing_order:
                    return OrderResult(
                        orderId=existing_order.id,
                        decisionId=decision_id,
                        clientOrderId=existing_order.client_order_id,
                        status=existing_order.status, # type: ignore
                        avgPrice=existing_order.avg_price,
                        qty=existing_order.qty,
                        broker="ALPACA_PAPER",
                        rawResponse=existing_order.raw_payload,
                    )

            return order_result

    async def reject_decision(self, decision_id: str) -> bool:
        lock = await _get_decision_lock(decision_id)
        async with lock:
            db_model = await self.dec_repo.get_by_id(decision_id)
            if not db_model:
                raise ValueError(f"Decision '{decision_id}' not found.")

            packet = DecisionPacket.model_validate(db_model.packet_json)
            
            # Lifecycle validation: cannot reject already approved/executed decisions
            if packet.status in ["APPROVED", "EXECUTED"]:
                raise ValueError(f"Lifecycle Gate Rejected: Decision '{decision_id}' is already '{packet.status}' and cannot be rejected.")

            packet.status = "REJECTED"
            await self.dec_repo.save(packet)
            await self.session.commit()
            logger.info(f"[{decision_id}] Trade proposal rejected by trader.")
            return True

    async def get_order_status(self, order_id: str) -> OrderResult:
        order_model = await self.order_repo.get_order_by_id(order_id)
        if order_model:
            return OrderResult(
                orderId=order_model.id,
                decisionId=order_model.decision_id,
                clientOrderId=order_model.client_order_id,
                status=order_model.status, # type: ignore
                avgPrice=order_model.avg_price,
                qty=order_model.qty,
                broker="ALPACA_PAPER",
                rawResponse=order_model.raw_payload,
            )

        return await self.broker.get_order(order_id)
