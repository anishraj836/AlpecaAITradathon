/**
 * VOLTRON API Client Layer
 * Single boundary for all frontend data access.
 * Switches seamlessly between MockApiAdapter and HttpSseApiAdapter.
 */

import {
  DecisionPacket,
  VolatilitySurface,
  StrategyCandidate,
  StressReport,
  AgentTraceStep,
  TelemetryStatus,
  ActiveOperationState,
  HistoricalDecisionSummary,
  CounterfactualComparison,
  OrderResult,
  MandatePipelineStep,
  PortfolioSummary,
} from '@/types/voltron';

import {
  DEMO_TELEMETRY,
  DEMO_DECISION_PACKET,
  DEMO_VOL_SURFACE,
  DEMO_STRATEGY_CANDIDATES,
  DEMO_STRESS_REPORT,
  DEMO_AGENT_TRACE,
  DEMO_ACTIVE_OPERATION,
  DEMO_DECISION_HISTORY,
  DEMO_COUNTERFACTUAL,
} from '@/fixtures/voltronFixtures';

export interface ApiClient {
  getTelemetry(): Promise<TelemetryStatus>;
  getPortfolio(): Promise<PortfolioSummary>;
  getDecision(id: string): Promise<DecisionPacket>;
  approveDecision(id: string): Promise<OrderResult>;
  rejectDecision(id: string): Promise<{ success: boolean; decisionId: string }>;
  getVolSurface(underlying?: string): Promise<VolatilitySurface>;
  getStrategyCandidates(underlying?: string): Promise<StrategyCandidate[]>;
  getStressReport(strategyId?: string): Promise<StressReport>;
  getAgentTrace(decisionId?: string): Promise<AgentTraceStep[]>;
  getActiveOperation(): Promise<ActiveOperationState>;
  getHistoricalDecisions(): Promise<HistoricalDecisionSummary[]>;
  getCounterfactual(params?: Record<string, unknown>): Promise<CounterfactualComparison>;
  dispatchMandate(
    mandate: string,
    onProgress?: (step: MandatePipelineStep) => void
  ): Promise<{ operationId: string; decisionId: string }>;
}

/**
 * Deterministic Mock Adapter for standalone frontend development and offline mode.
 * All fixture values are strictly isolated and labeled as demo state.
 */
class MockApiAdapter implements ApiClient {
  private mockDecisionState: DecisionPacket = { ...DEMO_DECISION_PACKET };

  async getTelemetry(): Promise<TelemetryStatus> {
    return { ...DEMO_TELEMETRY, timestamp: new Date().toLocaleTimeString('en-US', { timeZone: 'America/New_York' }) + ' EST' };
  }

  async getPortfolio(): Promise<PortfolioSummary> {
    return {
      account: {
        accountId: 'demo-alpaca-paper',
        status: 'ACTIVE',
        currency: 'USD',
        cash: 100000.0,
        equity: 100000.0,
        buyingPower: 200000.0,
        isPaper: true,
      },
      positions: [
        { symbol: 'SPY260918P00625000', qty: 1, side: 'long', marketValue: 110.0, avgEntryPrice: 1.08, unrealizedPl: 2.0, currentPrice: 1.10 },
        { symbol: 'SPY260918P00630000', qty: -1, side: 'short', marketValue: -186.0, avgEntryPrice: 1.84, unrealizedPl: -2.0, currentPrice: 1.86 },
        { symbol: 'SPY260918C00660000', qty: -1, side: 'short', marketValue: -150.0, avgEntryPrice: 1.48, unrealizedPl: -2.0, currentPrice: 1.50 },
        { symbol: 'SPY260918C00665000', qty: 1, side: 'long', marketValue: 88.0, avgEntryPrice: 0.86, unrealizedPl: 2.0, currentPrice: 0.88 },
      ],
      netDelta: 0.12,
      netTheta: 48.50,
      netVega: -12.40,
      netGamma: 0.008,
      unrealizedPnl: 84.00,
      realizedTodayPnl: 138.00,
      profitTargetPct: 50.0,
      stopLossMultiplier: 2.0,
    };
  }

  async getDecision(id: string): Promise<DecisionPacket> {
    return { ...this.mockDecisionState, id: id || this.mockDecisionState.id };
  }

  async approveDecision(id: string): Promise<OrderResult> {
    this.mockDecisionState.status = 'APPROVED';
    return {
      orderId: `ALP-ORD-${Math.random().toString(36).substring(2, 9).toUpperCase()}`,
      decisionId: id,
      clientOrderId: `cl-${id}-${Date.now()}`,
      status: 'accepted',
      avgPrice: this.mockDecisionState.strategy.netCreditOrDebit,
      qty: 1,
      broker: 'ALPACA_PAPER',
      filledAt: new Date().toISOString(),
    };
  }

  async rejectDecision(id: string): Promise<{ success: boolean; decisionId: string }> {
    this.mockDecisionState.status = 'REJECTED';
    return { success: true, decisionId: id };
  }

  async getVolSurface(underlying: string = 'SPY'): Promise<VolatilitySurface> {
    return { ...DEMO_VOL_SURFACE, underlying };
  }

  async getStrategyCandidates(underlying: string = 'SPY'): Promise<StrategyCandidate[]> {
    return DEMO_STRATEGY_CANDIDATES.map((c) => ({ ...c, underlying }));
  }

  async getStressReport(strategyId: string = 'strat-condor-01'): Promise<StressReport> {
    return { ...DEMO_STRESS_REPORT, strategyId };
  }

  async getAgentTrace(decisionId: string = 'DEC-SPY-9942'): Promise<AgentTraceStep[]> {
    return DEMO_AGENT_TRACE;
  }

  async getActiveOperation(): Promise<ActiveOperationState> {
    return DEMO_ACTIVE_OPERATION;
  }

  async getHistoricalDecisions(): Promise<HistoricalDecisionSummary[]> {
    return DEMO_DECISION_HISTORY;
  }

  async getCounterfactual(params?: Record<string, unknown>): Promise<CounterfactualComparison> {
    if (!params || Object.keys(params).length === 0) {
      return DEMO_COUNTERFACTUAL;
    }
    const targetDelta = typeof params.targetDelta === 'number' ? params.targetDelta : DEMO_COUNTERFACTUAL.scenario.targetDelta;
    const dteDays = typeof params.dteDays === 'number' ? params.dteDays : DEMO_COUNTERFACTUAL.scenario.dteDays;
    const budget = typeof params.budget === 'number' ? params.budget : DEMO_COUNTERFACTUAL.scenario.allocatedBudget;
    return {
      ...DEMO_COUNTERFACTUAL,
      scenario: {
        ...DEMO_COUNTERFACTUAL.scenario,
        targetDelta,
        dteDays,
        allocatedBudget: budget,
        winningStrategy: {
          ...DEMO_COUNTERFACTUAL.scenario.winningStrategy,
          dte: dteDays,
        },
      },
    };
  }

  async dispatchMandate(
    mandate: string,
    onProgress?: (step: MandatePipelineStep) => void
  ): Promise<{ operationId: string; decisionId: string }> {
    const opId = `OP-${Math.floor(1000 + Math.random() * 9000)}`;
    const decId = `DEC-SPY-${Math.floor(1000 + Math.random() * 9000)}`;

    if (onProgress) {
      setTimeout(() => {
        onProgress({
          id: 'step-1',
          title: 'Fetching market context',
          status: 'COMPLETE',
          durationMs: 120,
          outputSummary: ['OK: SPY 645.31', 'OK: VIX 18.2'],
        });
      }, 200);

      setTimeout(() => {
        onProgress({
          id: 'step-2',
          title: 'Reading option surface',
          status: 'ACTIVE',
        });
      }, 400);
    }

    return { operationId: opId, decisionId: decId };
  }
}

/**
 * Live HTTP + SSE Adapter connecting to the FastAPI Backend and Orchestrator.
 */
class HttpSseApiAdapter implements ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
  }

  private async fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`API Request to ${path} failed (${res.status}): ${errorText}`);
    }
    return res.json();
  }

  async getTelemetry(): Promise<TelemetryStatus> {
    try {
      return await this.fetchJson<TelemetryStatus>('/telemetry');
    } catch {
      return { ...DEMO_TELEMETRY, timestamp: new Date().toLocaleTimeString('en-US') + ' EST' };
    }
  }

  async getPortfolio(): Promise<PortfolioSummary> {
    try {
      return await this.fetchJson<PortfolioSummary>('/portfolio');
    } catch {
      return new MockApiAdapter().getPortfolio();
    }
  }

  async getDecision(id: string): Promise<DecisionPacket> {
    return this.fetchJson<DecisionPacket>(`/decisions/${id}`);
  }

  async approveDecision(id: string): Promise<OrderResult> {
    return this.fetchJson<OrderResult>(`/decisions/${id}/approve`, { method: 'POST' });
  }

  async rejectDecision(id: string): Promise<{ success: boolean; decisionId: string }> {
    return this.fetchJson<{ success: boolean; decisionId: string }>(`/decisions/${id}/reject`, { method: 'POST' });
  }

  async getVolSurface(underlying: string = 'SPY'): Promise<VolatilitySurface> {
    return this.fetchJson<VolatilitySurface>(`/quant/surface?symbol=${underlying}`);
  }

  async getStrategyCandidates(underlying: string = 'SPY'): Promise<StrategyCandidate[]> {
    return this.fetchJson<StrategyCandidate[]>(`/quant/strategies?symbol=${underlying}`);
  }

  async getStressReport(strategyId: string = 'strat-condor-01'): Promise<StressReport> {
    return this.fetchJson<StressReport>(`/quant/stress?strategy_id=${strategyId}`);
  }

  async getAgentTrace(decisionId: string = 'DEC-SPY-9942'): Promise<AgentTraceStep[]> {
    return this.fetchJson<AgentTraceStep[]>(`/quant/agents/trace/${decisionId}`);
  }

  async getActiveOperation(): Promise<ActiveOperationState> {
    return DEMO_ACTIVE_OPERATION;
  }

  async getHistoricalDecisions(): Promise<HistoricalDecisionSummary[]> {
    return this.fetchJson<HistoricalDecisionSummary[]>('/history');
  }

  async getCounterfactual(params?: Record<string, unknown>): Promise<CounterfactualComparison> {
    return this.fetchJson<CounterfactualComparison>('/quant/counterfactual', {
      method: 'POST',
      body: JSON.stringify(params || {}),
    });
  }

  async dispatchMandate(
    mandate: string,
    onProgress?: (step: MandatePipelineStep) => void
  ): Promise<{ operationId: string; decisionId: string }> {
    let eventSource: EventSource | null = null;
    
    // Connect to SSE stream if running in browser
    if (typeof window !== 'undefined' && typeof EventSource !== 'undefined' && onProgress) {
      try {
        eventSource = new EventSource(`${this.baseUrl}/stream/orchestrator`);
        eventSource.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data);
            if (parsed.stage) {
              const stepMap: Record<string, string> = {
                INIT: 'step-1',
                DATA_FETCH: 'step-2',
                RESEARCH: 'step-3',
                VOLATILITY: 'step-4',
                STRATEGY: 'step-5',
                CRITIC: 'step-6',
                RISK: 'step-7',
                COMPLETE: 'step-7',
              };
              const stepId = stepMap[parsed.stage] || 'step-1';
              onProgress({
                id: stepId,
                title: parsed.message || parsed.stage,
                status: parsed.status === 'COMPLETE' ? 'COMPLETE' : 'ACTIVE',
                outputSummary: [parsed.message],
              });
            }
          } catch {
            // Ignore non-json chunks
          }
        };
      } catch {
        // Fallback gracefully if EventSource not supported
      }
    }

    try {
      // 1. Submit mandate to FastAPI /api/scan endpoint
      const packet = await this.fetchJson<DecisionPacket>('/scan', {
        method: 'POST',
        body: JSON.stringify({ mandate, underlying: 'SPY' }),
      });

      // 2. Notify final progress completion
      if (onProgress) {
        onProgress({
          id: 'step-7',
          title: 'Decision Complete',
          status: 'COMPLETE',
          outputSummary: [`Winner: ${packet.strategy.name}`, `Score: ${packet.strategy.score.toFixed(1)}`],
        });
      }

      return {
        operationId: `OP-${packet.id}`,
        decisionId: packet.id,
      };
    } finally {
      if (eventSource) {
        eventSource.close();
      }
    }
  }
}

// Config-based singleton export
const useMocks = process.env.NEXT_PUBLIC_USE_MOCKS !== 'false';
export const api: ApiClient = useMocks ? new MockApiAdapter() : new HttpSseApiAdapter();
