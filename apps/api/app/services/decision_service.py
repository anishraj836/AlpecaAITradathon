from typing import Optional, List
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import DecisionPacket, OrderResult, DecisionStatus
from app.infrastructure.database.repositories.decisions import DecisionRepository
from app.infrastructure.alpaca.gateway import BrokerGateway
from app.infrastructure.options.gateway import OptionsIntelligenceGateway

class DecisionService:
    def __init__(
        self,
        session: AsyncSession,
        broker_gateway: BrokerGateway,
        quant_gateway: OptionsIntelligenceGateway,
    ):
        self.session = session
        self.repo = DecisionRepository(session)
        self.broker_gateway = broker_gateway
        self.quant_gateway = quant_gateway

    async def get_decision(self, decision_id: str) -> DecisionPacket:
        db_model = await self.repo.get_by_id(decision_id)
        if db_model:
            return DecisionPacket.model_validate(db_model.packet_json)

        # Allow fallback and persistence only for explicit demo ID
        if decision_id == "DEC-SPY-9942":
            strategy = (await self.quant_gateway.generate_candidates("SPY"))[0]
            account = await self.broker_gateway.get_account()
            risk_result = await self.quant_gateway.compile_risk(strategy, account.equity)

            packet = DecisionPacket(
                id=decision_id,
                createdAt="2026-08-29T10:45:12Z",
                underlying="SPY",
                spotPrice=645.31,
                marketRegime="Range-Bound",
                iv30=18.4,
                ivRank=72.1,
                aiConfidence=0.81,
                strategy=strategy,
                evidence={
                    "description": "Elevated put skew detected relative to historical mean. Term structure indicates near-term premium richness.",
                    "putSkewElevated": True,
                    "termStructureRich": True,
                },
                whyThisTrade=[
                    "Expected to remain range-bound post-earnings season.",
                    "Captures volatility skew advantage on both wings.",
                    "Strictly defined risk fits current portfolio delta targets.",
                ],
                criticAnalysis={
                    "primaryFailureMode": "Upside breakout beyond 665.",
                    "details": "Macro indicators suggest persistent tech sector momentum could push SPY past call wing strikes before expiry.",
                },
                riskCompilerResult=risk_result,
                status="AWAITING_APPROVAL",
            )
            await self.repo.save(packet)
            await self.session.commit()
            return packet

        raise HTTPException(status_code=404, detail=f"Decision '{decision_id}' not found.")

    async def approve_decision(self, decision_id: str) -> OrderResult:
        packet = await self.get_decision(decision_id)
        
        # Verify Deterministic Risk Compiler Gate
        if not packet.riskCompilerResult.isApproved:
            raise ValueError(f"Deterministic Risk Compiler violation: Decision {decision_id} failed risk checks.")

        # Execute Order via Paper Broker Gateway
        order_result = await self.broker_gateway.place_multileg_order(packet)

        # Update decision status to APPROVED
        packet.status = "APPROVED"
        await self.repo.save(packet)
        await self.session.commit()
        return order_result

    async def reject_decision(self, decision_id: str) -> bool:
        packet = await self.get_decision(decision_id)
        packet.status = "REJECTED"
        await self.repo.save(packet)
        await self.session.commit()
        return True
