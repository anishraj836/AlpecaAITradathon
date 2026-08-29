from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.infrastructure.database.session import Base

def _utc_now():
    return datetime.now(timezone.utc)

class MarketSnapshotModel(Base):
    __tablename__ = "market_snapshots"

    id = Column(String(64), primary_key=True, index=True)
    symbol = Column(String(16), index=True, nullable=False)
    price = Column(Float, nullable=False)
    change_pct = Column(Float, nullable=False)
    iv30 = Column(Float, nullable=True)
    iv_rank = Column(Float, nullable=True)
    regime = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=_utc_now, nullable=False, index=True)
    raw_payload = Column(JSON, nullable=True)

class OptionSnapshotModel(Base):
    __tablename__ = "option_snapshots"

    id = Column(String(64), primary_key=True, index=True)
    underlying = Column(String(16), index=True, nullable=False)
    contract_symbol = Column(String(64), index=True, nullable=False)
    strike = Column(Float, nullable=False)
    dte = Column(Integer, nullable=False)
    option_type = Column(String(8), nullable=False) # CALL/PUT
    bid = Column(Float, nullable=False)
    ask = Column(Float, nullable=False)
    mid = Column(Float, nullable=False)
    iv = Column(Float, nullable=False)
    delta = Column(Float, nullable=False)
    gamma = Column(Float, nullable=True)
    theta = Column(Float, nullable=True)
    vega = Column(Float, nullable=True)
    created_at = Column(DateTime, default=_utc_now, nullable=False, index=True)

class DecisionModel(Base):
    __tablename__ = "decisions"

    id = Column(String(64), primary_key=True, index=True)
    underlying = Column(String(16), index=True, nullable=False)
    spot_price = Column(Float, nullable=False)
    market_regime = Column(String(32), nullable=False)
    iv30 = Column(Float, nullable=False)
    iv_rank = Column(Float, nullable=False)
    ai_confidence = Column(Float, nullable=False)
    status = Column(String(32), index=True, nullable=False) # AWAITING_APPROVAL, APPROVED, REJECTED, EXECUTED
    created_at = Column(DateTime, default=_utc_now, nullable=False, index=True)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now, nullable=False)
    
    # Serialized complete decision packet JSON
    packet_json = Column(JSON, nullable=False)

    # Relationships
    candidates = relationship("StrategyCandidateModel", back_populates="decision", cascade="all, delete-orphan")
    risk_checks = relationship("RiskCheckModel", back_populates="decision", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRunModel", back_populates="decision", cascade="all, delete-orphan")
    orders = relationship("OrderModel", back_populates="decision", cascade="all, delete-orphan")

class StrategyCandidateModel(Base):
    __tablename__ = "strategy_candidates"

    id = Column(String(64), primary_key=True, index=True)
    decision_id = Column(String(64), ForeignKey("decisions.id"), nullable=False, index=True)
    name = Column(String(64), nullable=False)
    dte = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    pop = Column(Float, nullable=False)
    max_profit = Column(Float, nullable=False)
    max_loss = Column(Float, nullable=False)
    net_credit = Column(Float, nullable=False)
    liquidity_score = Column(Integer, nullable=False)
    is_winner = Column(Boolean, default=False, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    legs_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False, index=True)

    decision = relationship("DecisionModel", back_populates="candidates")

class RiskCheckModel(Base):
    __tablename__ = "risk_checks"

    id = Column(String(64), primary_key=True, index=True)
    decision_id = Column(String(64), ForeignKey("decisions.id"), nullable=False, index=True)
    is_approved = Column(Boolean, nullable=False)
    budget_pass = Column(Boolean, nullable=False)
    liquidity_pass = Column(Boolean, nullable=False)
    concentration_pass = Column(Boolean, nullable=False)
    check_details_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False, index=True)

    decision = relationship("DecisionModel", back_populates="risk_checks")

class AgentRunModel(Base):
    __tablename__ = "agent_runs"

    id = Column(String(64), primary_key=True, index=True)
    decision_id = Column(String(64), ForeignKey("decisions.id"), nullable=False, index=True)
    agent_role = Column(String(32), nullable=False)
    title = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)
    elapsed_ms = Column(Integer, nullable=True)
    summary = Column(Text, nullable=False)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utc_now, nullable=False, index=True)

    decision = relationship("DecisionModel", back_populates="agent_runs")

class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(String(64), primary_key=True, index=True)
    decision_id = Column(String(64), ForeignKey("decisions.id"), nullable=False, index=True)
    client_order_id = Column(String(64), unique=True, index=True, nullable=False)
    broker_order_id = Column(String(64), unique=True, index=True, nullable=True)
    symbol = Column(String(16), nullable=False)
    order_type = Column(String(16), nullable=False)
    status = Column(String(32), nullable=False) # pending, accepted, filled, rejected
    avg_price = Column(Float, nullable=False)
    qty = Column(Integer, default=1, nullable=False)
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utc_now, nullable=False, index=True)

    decision = relationship("DecisionModel", back_populates="orders")
    fills = relationship("FillModel", back_populates="order", cascade="all, delete-orphan")

class FillModel(Base):
    __tablename__ = "fills"

    id = Column(String(64), primary_key=True, index=True)
    order_id = Column(String(64), ForeignKey("orders.id"), nullable=False, index=True)
    broker_exec_id = Column(String(64), nullable=True)
    fill_price = Column(Float, nullable=False)
    qty = Column(Integer, nullable=False)
    filled_at = Column(DateTime, default=_utc_now, nullable=False, index=True)

    order = relationship("OrderModel", back_populates="fills")
