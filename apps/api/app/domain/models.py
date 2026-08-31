from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

OptionType = Literal['CALL', 'PUT']
PositionSide = Literal['BUY', 'SELL']
OptionPositionIntent = Literal['buy_to_open', 'sell_to_open', 'buy_to_close', 'sell_to_close']
AgentRole = Literal['RESEARCHER', 'VOLATILITY_ANALYST', 'STRATEGY_ANALYST', 'CRITIC', 'RISK_COMPILER']
AutonomyLevel = Literal['COPILOT', 'GUARDED_AUTONOMOUS', 'AUTOPILOT']
ExecutionMode = Literal['LLM_REASONING', 'HEURISTIC_FALLBACK']
DecisionStatus = Literal[
    'CREATED',
    'ANALYZING',
    'DECISION_READY',
    'AWAITING_APPROVAL',
    'APPROVED',
    'REJECTED',
    'EXECUTED',
    'FAILED',
    'NO_TRADE',
]

class OptionLeg(BaseModel):
    id: str
    symbol: str
    underlying: str
    expiration: str
    dte: int
    strike: float
    type: OptionType
    side: PositionSide
    ratio: int = 1
    bid: float
    ask: float
    mid: float
    last: Optional[float] = None
    iv: float = 0.20
    delta: float = 0.50
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0

class StrategyCandidate(BaseModel):
    id: str
    name: str
    underlying: str
    dte: int
    score: float
    pop: float
    maxProfit: float
    maxLoss: float
    netCreditOrDebit: float
    liquidityScore: int
    legs: List[OptionLeg] = Field(default_factory=list)
    breakevens: List[float] = Field(default_factory=list)
    rationale: List[str] = Field(default_factory=list)
    isWinner: bool = False
    rejectionReason: Optional[str] = None
    rank: Optional[int] = None

class VolatilitySurfacePoint(BaseModel):
    strike: float
    dte: int
    iv: float
    delta: float
    volume: int
    openInterest: int

class TermStructurePoint(BaseModel):
    dte: int
    label: str
    dateLabel: str
    iv: float
    percentageOfMax: float

class SkewSnapshot(BaseModel):
    put25DeltaIV: float
    atmIV: float
    call25DeltaIV: float
    skewRatio: float

class AnomalyReport(BaseModel):
    id: str
    name: str
    description: str
    percentile: float
    confidence: Literal['LOW', 'MED', 'HIGH']
    category: Literal['SKEW', 'TERM', 'LIQUIDITY', 'VOL_SPIKE']
    metricLabel: str

class VolatilitySurface(BaseModel):
    underlying: str
    spotPrice: float
    changePct: float
    timestamp: str
    points: List[VolatilitySurfacePoint] = Field(default_factory=list)
    termStructure: List[TermStructurePoint] = Field(default_factory=list)
    skewSnapshot: SkewSnapshot
    anomalies: List[AnomalyReport] = Field(default_factory=list)

class StressMatrixCell(BaseModel):
    priceShiftPct: float
    ivShiftPct: float
    pnl: float

class MaxProfitZone(BaseModel):
    minPrice: float
    maxPrice: float
    maxPnl: float

class ModelAssumptions(BaseModel):
    riskBudget: float
    targetDelta: float
    evaluationHorizonDays: int
    volRegime: str

class StressReport(BaseModel):
    strategyId: str
    modelId: str
    baselinePnl: float
    matrix: List[StressMatrixCell] = Field(default_factory=list)
    maxProfitZone: MaxProfitZone
    assumptions: ModelAssumptions

class Tag(BaseModel):
    label: str
    variant: Literal['primary', 'secondary', 'tertiary', 'error', 'warning']

class MetricRow(BaseModel):
    label: str
    current: str
    baseline: str

class EvaluatedStructure(BaseModel):
    name: str
    score: float
    isSelected: bool

class RiskMetric(BaseModel):
    label: str
    value: str

class AgentTraceDetails(BaseModel):
    keyDrivers: Optional[List[str]] = None
    metrics: Optional[List[MetricRow]] = None
    recommendations: Optional[List[str]] = None
    evaluatedStructures: Optional[List[EvaluatedStructure]] = None
    riskMetrics: Optional[List[RiskMetric]] = None

class AgentTraceStep(BaseModel):
    id: str
    agentRole: AgentRole
    agentLabel: str
    title: str
    timestampOffset: str
    status: Literal['PENDING', 'ACTIVE', 'COMPLETE', 'FAILED']
    summary: str
    confidenceScore: Optional[float] = None
    tags: List[Tag] = Field(default_factory=list)
    details: Optional[AgentTraceDetails] = None
    executionMode: Optional[ExecutionMode] = "LLM_REASONING"
    providerName: Optional[str] = None
    modelName: Optional[str] = None

class RiskCheckItem(BaseModel):
    passed: bool
    status: Literal['PASS', 'WARN', 'FAIL']
    label: str
    valueText: str
    details: Optional[str] = None

class RiskCheckResult(BaseModel):
    budgetCheck: RiskCheckItem
    liquidityCheck: RiskCheckItem
    concentrationCheck: RiskCheckItem
    isApproved: bool

class EvidenceContext(BaseModel):
    description: str
    putSkewElevated: bool
    termStructureRich: bool

class CriticAnalysis(BaseModel):
    primaryFailureMode: str
    details: str

class MlegOrderLegPayload(BaseModel):
    symbol: str
    ratio_qty: int = 1
    side: Literal['buy', 'sell']
    position_intent: OptionPositionIntent

class MlegOrderPayload(BaseModel):
    symbol: str
    orderType: Literal['limit', 'market'] = 'limit'
    timeInForce: Literal['day'] = 'day'
    limitPrice: Optional[float] = None
    legs: List[MlegOrderLegPayload]

class DecisionPacket(BaseModel):
    id: str
    createdAt: str
    underlying: str
    spotPrice: float
    marketRegime: str
    iv30: float
    ivRank: float
    aiConfidence: float
    strategy: StrategyCandidate
    evidence: EvidenceContext
    whyThisTrade: List[str]
    criticAnalysis: CriticAnalysis
    riskCompilerResult: RiskCheckResult
    status: DecisionStatus
    mlegOrderPayload: Optional[MlegOrderPayload] = None
    autonomyLevel: Optional[AutonomyLevel] = "GUARDED_AUTONOMOUS"
    isDegradedMode: bool = False
    llmProvider: Optional[str] = None
    llmModel: Optional[str] = None
    degradedReason: Optional[str] = None

class OrderResult(BaseModel):
    orderId: str
    decisionId: str
    clientOrderId: str
    status: Literal['filled', 'accepted', 'rejected', 'pending', 'submitted']
    filledAt: Optional[str] = None
    avgPrice: float
    qty: int = 1
    broker: str = "ALPACA_PAPER"
    rawResponse: Optional[Dict[str, Any]] = None

class TelemetryStatus(BaseModel):
    marketStatus: Literal['OPEN', 'CLOSED', 'PRE', 'POST']
    underlying: str
    underlyingPrice: float
    underlyingChangePct: float
    accountEquity: float
    buyingPower: float
    alpacaConnected: bool
    isPaper: bool
    timestamp: str

class AccountInfo(BaseModel):
    accountId: str
    status: str
    currency: str
    cash: float
    portfolioValue: float
    equity: float
    buyingPower: float
    patternDayTrader: bool
    optionsTradingLevel: int
    isPaper: bool

class PositionInfo(BaseModel):
    symbol: str
    qty: float
    side: Literal['long', 'short']
    marketValue: float
    avgEntryPrice: float
    unrealizedPl: float
    currentPrice: float

class PortfolioSummary(BaseModel):
    account: AccountInfo
    positions: List[PositionInfo] = Field(default_factory=list)
    netDelta: float = 0.12
    netTheta: float = 48.50
    netVega: float = -12.40
    netGamma: float = 0.008
    unrealizedPnl: float = 84.00
    realizedTodayPnl: float = 138.00
    profitTargetPct: float = 50.0
    stopLossMultiplier: float = 2.0

class MarketContext(BaseModel):
    symbol: str
    price: float
    changePct: float
    high: float
    low: float
    volume: int
    vwap: Optional[float] = None
    timestamp: str
    news: Optional[List[Dict[str, Any]]] = None

class MandatePipelineStep(BaseModel):
    id: str
    title: str
    status: Literal['COMPLETE', 'ACTIVE', 'PENDING', 'FAILED']
    durationMs: Optional[int] = None
    outputSummary: Optional[List[str]] = None

class ActiveOperationState(BaseModel):
    operationId: str
    mandate: str
    underlying: str
    status: Literal['IDLE', 'PROCESSING', 'COMPLETED', 'FAILED']
    currentStepIndex: int
    steps: List[MandatePipelineStep]
    estTimeRemainingSec: Optional[float] = None
    decisionId: Optional[str] = None

class HistoricalDecisionSummary(BaseModel):
    id: str
    timestamp: str
    timeFormatted: str
    symbol: str
    strategyName: str
    decision: Literal['Approved', 'No Trade', 'Rejected']
    riskAmount: float
    outcomeAmount: float
    isProfit: bool
    pop: float
    legsSummary: str

class CounterfactualBaseline(BaseModel):
    targetDelta: float
    dteDays: int
    allocatedBudget: float
    winningStrategy: StrategyCandidate

class CounterfactualScenario(BaseModel):
    targetDelta: float
    dteDays: int
    allocatedBudget: float
    winningStrategy: StrategyCandidate
    reasoning: List[str]

class CounterfactualComparison(BaseModel):
    baseline: CounterfactualBaseline
    scenario: CounterfactualScenario

class MandateRequest(BaseModel):
    mandate: str
    underlying: Optional[str] = "SPY"
    autonomyLevel: Optional[AutonomyLevel] = None

class ApprovalRequest(BaseModel):
    decisionId: str
    notes: Optional[str] = None

class SystemSettings(BaseModel):
    llmProvider: str
    llmModel: str
    isApiKeyConfigured: bool
    apiKeyMasked: Optional[str] = None
    autonomyLevel: AutonomyLevel = "GUARDED_AUTONOMOUS"
    availableProviders: List[str] = Field(default_factory=lambda: [
        "gemini", "openai", "groq", "anthropic", "deepseek", "ollama", "custom"
    ])
    availableModels: Dict[str, List[str]] = Field(default_factory=lambda: {
        "gemini": ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-2.5-flash", "gemini-2.5-pro"],
        "openai": ["gpt-4o-mini", "gpt-4o", "o3-mini", "gpt-4-turbo"],
        "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "anthropic": ["claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022"],
        "deepseek": ["deepseek-chat", "deepseek-reasoner"],
        "ollama": ["llama3.2:3b", "qwen2.5:3b", "mistral:7b"],
        "custom": ["default"],
    })

class UpdateSettingsRequest(BaseModel):
    llmProvider: Optional[str] = None
    llmModel: Optional[str] = None
    apiKey: Optional[str] = None
    baseUrl: Optional[str] = None
    autonomyLevel: Optional[AutonomyLevel] = None

class TestConnectionRequest(BaseModel):
    provider: str
    model: Optional[str] = None
    apiKey: Optional[str] = None
    baseUrl: Optional[str] = None

class TestConnectionResponse(BaseModel):
    success: bool
    provider: str
    model: str
    message: str
    latencyMs: Optional[int] = None

# ==========================================
# Runtime Multi-Agent Communication Contracts
# ==========================================

class MarketResearch(BaseModel):
    symbol: str
    spotPrice: float
    marketRegimeSummary: str
    eventFlags: List[str] = Field(default_factory=list)
    relevantEvidence: List[str] = Field(default_factory=list)
    confidence: float
    summary: str

class VolatilityAnalysis(BaseModel):
    symbol: str
    keyAnomaly: str
    skewInterpretation: str
    termStructureInterpretation: str
    confidence: float
    evidence: List[str] = Field(default_factory=list)
    caveats: List[str] = Field(default_factory=list)
    summary: str

class StrategySelection(BaseModel):
    selectedCandidateId: str
    candidateName: str
    reasoning: List[str] = Field(default_factory=list)
    confidence: float
    rejectedCandidateNotes: Dict[str, str] = Field(default_factory=dict)

class Critique(BaseModel):
    verdict: Literal['APPROVED_WITH_CONDITIONS', 'REJECTED', 'APPROVED']
    primaryFailureMode: str
    severity: Literal['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    failureScenarios: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence: float
    details: str

class OrchestratorEvent(BaseModel):
    decisionId: str
    eventType: str
    stage: str
    status: Literal['PENDING', 'ACTIVE', 'COMPLETE', 'FAILED']
    message: str
    timestamp: str
    payload: Optional[Dict[str, Any]] = None
