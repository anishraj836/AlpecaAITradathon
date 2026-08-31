/**
 * Canonical VOLTRON Data Contracts & DTOs
 * Mirrored 1-to-1 from backend Pydantic models (apps/api/app/domain/models.py).
 * 
 * Rules:
 * - Person 1 owns canonical financial computations in packages/options-alpha-mcp/.
 * - Frontend strictly handles presentation and human-in-the-loop interactions.
 * - Zero duplicated Black-Scholes or Greeks calculations in TypeScript.
 */

export type OptionType = 'CALL' | 'PUT';
export type PositionSide = 'BUY' | 'SELL';
export type OptionPositionIntent = 'buy_to_open' | 'sell_to_open' | 'buy_to_close' | 'sell_to_close';

export type DecisionStatus =
  | 'CREATED'
  | 'ANALYZING'
  | 'DECISION_READY'
  | 'AWAITING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED'
  | 'EXECUTED'
  | 'FAILED'
  | 'NO_TRADE';

export interface OptionLeg {
  id: string;
  symbol: string;
  underlying: string;
  expiration: string;
  dte: number;
  strike: number;
  type: OptionType;
  side: PositionSide;
  ratio: number;
  bid: number;
  ask: number;
  mid: number;
  last?: number;
  iv: number;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
}

export interface StrategyCandidate {
  id: string;
  name: string;
  underlying: string;
  dte: number;
  score: number;
  pop: number; // Probability of Profit (0.0 - 1.0)
  maxProfit: number;
  maxLoss: number;
  netCreditOrDebit: number; // Positive = Credit, Negative = Debit
  liquidityScore: number; // 0 - 100
  legs: OptionLeg[];
  breakevens: number[];
  rationale: string[];
  isWinner?: boolean;
  rejectionReason?: string;
  rank?: number;
}

export interface VolatilitySurfacePoint {
  strike: number;
  dte: number;
  iv: number;
  delta: number;
  volume: number;
  openInterest: number;
}

export interface TermStructurePoint {
  dte: number;
  label: string;
  dateLabel: string;
  iv: number;
  percentageOfMax: number;
}

export interface SkewSnapshot {
  put25DeltaIV: number;
  atmIV: number;
  call25DeltaIV: number;
  skewRatio: number;
}

export interface AnomalyReport {
  id: string;
  name: string;
  description: string;
  percentile: number;
  confidence: 'LOW' | 'MED' | 'HIGH';
  category: 'SKEW' | 'TERM' | 'LIQUIDITY' | 'VOL_SPIKE';
  metricLabel: string;
}

export interface VolatilitySurface {
  underlying: string;
  spotPrice: number;
  changePct: number;
  timestamp: string;
  points: VolatilitySurfacePoint[];
  termStructure: TermStructurePoint[];
  skewSnapshot: SkewSnapshot;
  anomalies: AnomalyReport[];
}

export interface StressMatrixCell {
  priceShiftPct: number; // e.g. -3.0, -1.5, 0.0, 1.5, 3.0
  ivShiftPct: number;    // e.g. -20, 0, 20
  pnl: number;
}

export interface StressReport {
  strategyId: string;
  modelId: string;
  baselinePnl: number;
  matrix: StressMatrixCell[];
  maxProfitZone: {
    minPrice: number;
    maxPrice: number;
    maxPnl: number;
  };
  assumptions: {
    riskBudget: number;
    targetDelta: number;
    evaluationHorizonDays: number;
    volRegime: string;
  };
}

export type AgentRole =
  | 'RESEARCHER'
  | 'VOLATILITY_ANALYST'
  | 'STRATEGY_ANALYST'
  | 'CRITIC'
  | 'RISK_COMPILER';

export type AutonomyLevel = 'COPILOT' | 'GUARDED_AUTONOMOUS' | 'AUTOPILOT';
export type ExecutionMode = 'LLM_REASONING' | 'HEURISTIC_FALLBACK';

export interface AgentTraceStep {
  id: string;
  agentRole: AgentRole;
  agentLabel: string;
  title: string;
  timestampOffset: string;
  status: 'PENDING' | 'ACTIVE' | 'COMPLETE' | 'FAILED';
  summary: string;
  confidenceScore?: number;
  tags?: Array<{ label: string; variant: 'primary' | 'secondary' | 'tertiary' | 'error' | 'warning' }>;
  details?: {
    keyDrivers?: string[];
    metrics?: Array<{ label: string; current: string; baseline: string }>;
    recommendations?: string[];
    evaluatedStructures?: Array<{ name: string; score: number; isSelected: boolean }>;
    riskMetrics?: Array<{ label: string; value: string }>;
  };
  executionMode?: ExecutionMode;
  providerName?: string;
  modelName?: string;
}

export interface RiskCheckItem {
  passed: boolean;
  status: 'PASS' | 'WARN' | 'FAIL';
  label: string;
  valueText: string;
  details?: string;
}

export interface RiskCheckResult {
  budgetCheck: RiskCheckItem;
  liquidityCheck: RiskCheckItem;
  concentrationCheck: RiskCheckItem;
  isApproved: boolean;
}

export interface DecisionPacket {
  id: string;
  createdAt: string;
  underlying: string;
  spotPrice: number;
  marketRegime: string;
  iv30: number;
  ivRank: number;
  aiConfidence: number; // 0.0 - 1.0
  strategy: StrategyCandidate;
  evidence: {
    description: string;
    putSkewElevated: boolean;
    termStructureRich: boolean;
  };
  whyThisTrade: string[];
  criticAnalysis: {
    primaryFailureMode: string;
    details: string;
  };
  riskCompilerResult: RiskCheckResult;
  status: DecisionStatus;
  autonomyLevel?: AutonomyLevel;
  isDegradedMode?: boolean;
  llmProvider?: string;
  llmModel?: string;
  degradedReason?: string;
  mlegOrderPayload?: {
    symbol: string;
    orderType: 'limit' | 'market';
    timeInForce: 'day';
    limitPrice?: number;
    legs: Array<{
      symbol: string;
      ratio_qty: number;
      side: 'buy' | 'sell';
      position_intent: OptionPositionIntent;
    }>;
  };
}

export interface SystemSettings {
  llmProvider: string;
  llmModel: string;
  isApiKeyConfigured: boolean;
  apiKeyMasked?: string;
  autonomyLevel: AutonomyLevel;
  availableProviders: string[];
  availableModels: Record<string, string[]>;
}

export interface UpdateSettingsRequest {
  llmProvider?: string;
  llmModel?: string;
  apiKey?: string;
  baseUrl?: string;
  autonomyLevel?: AutonomyLevel;
}

export interface TestConnectionRequest {
  provider: string;
  model?: string;
  apiKey?: string;
  baseUrl?: string;
}

export interface TestConnectionResponse {
  success: boolean;
  provider: string;
  model: string;
  message: string;
  latencyMs?: number;
}

export interface OrderResult {
  orderId: string;
  decisionId: string;
  clientOrderId: string;
  status: 'filled' | 'accepted' | 'rejected' | 'pending' | 'submitted';
  filledAt?: string;
  avgPrice: number;
  qty: number;
  broker: 'ALPACA_PAPER' | 'ALPACA_LIVE';
  rawResponse?: Record<string, unknown>;
}

export interface TelemetryStatus {
  marketStatus: 'OPEN' | 'CLOSED' | 'PRE' | 'POST';
  underlying: string;
  underlyingPrice: number;
  underlyingChangePct: number;
  accountEquity: number;
  buyingPower: number;
  alpacaConnected: boolean;
  isPaper: boolean;
  timestamp: string;
}

export interface PositionInfo {
  symbol: string;
  qty: number;
  side: 'long' | 'short';
  marketValue: number;
  avgEntryPrice: number;
  unrealizedPl: number;
  currentPrice: number;
}

export interface AssetAllocation {
  symbol: string;
  assetClass: string;
  weightPct: number;
  allocatedAmount: number;
  currentPnl: number;
  beta: number;
  ivRank: number;
  strategyType: string;
}

export interface DiversificationAnalysis {
  diversificationScore: number;
  rating: string;
  betaWeightedDelta: number;
  hhiConcentration: number;
  maxSingleAssetPct: number;
  correlationMatrix: Record<string, Record<string, number>>;
  allocations: AssetAllocation[];
  rebalanceRecommendation?: string;
}

export interface PortfolioSummary {
  account: {
    accountId: string;
    status: string;
    currency: string;
    cash: number;
    equity: number;
    buyingPower: number;
    isPaper: boolean;
  };
  positions: PositionInfo[];
  netDelta: number;
  netTheta: number;
  netVega: number;
  netGamma: number;
  unrealizedPnl: number;
  realizedTodayPnl: number;
  profitTargetPct: number;
  stopLossMultiplier: number;
  diversification?: DiversificationAnalysis;
}

export interface MandatePipelineStep {
  id: string;
  title: string;
  status: 'COMPLETE' | 'ACTIVE' | 'PENDING' | 'FAILED';
  durationMs?: number;
  outputSummary?: string[];
}

export interface ActiveOperationState {
  operationId: string;
  mandate: string;
  underlying: string;
  status: 'IDLE' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  currentStepIndex: number;
  steps: MandatePipelineStep[];
  estTimeRemainingSec?: number;
  decisionId?: string;
}

export interface HistoricalDecisionSummary {
  id: string;
  timestamp: string;
  timeFormatted: string;
  symbol: string;
  strategyName: string;
  decision: 'Approved' | 'No Trade' | 'Rejected';
  riskAmount: number;
  outcomeAmount: number;
  isProfit: boolean;
  pop: number;
  legsSummary: string;
}

export interface CounterfactualComparison {
  baseline: {
    targetDelta: number;
    dteDays: number;
    allocatedBudget: number;
    winningStrategy: StrategyCandidate;
  };
  scenario: {
    targetDelta: number;
    dteDays: number;
    allocatedBudget: number;
    winningStrategy: StrategyCandidate;
    reasoning: string[];
  };
}

export interface OrchestratorEvent {
  decisionId: string;
  eventType: string;
  stage: string;
  status: 'PENDING' | 'ACTIVE' | 'COMPLETE' | 'FAILED';
  message: string;
  timestamp: string;
  payload?: Record<string, unknown>;
}
