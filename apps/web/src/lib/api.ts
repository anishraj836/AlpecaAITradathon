/**
 * VOLTRON API Client Layer
 * Real HTTP + SSE Client connecting directly to FastAPI Backend and Alpaca Gateway.
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
  PortfolioHistory,
  AnomalyReport,
} from '@/types/voltron';

export interface ApiClient {
  getTelemetry(): Promise<TelemetryStatus>;
  getPortfolio(): Promise<PortfolioSummary>;
  getPortfolioHistory(period?: string, timeframe?: string): Promise<PortfolioHistory>;
  rebalancePortfolio(): Promise<PortfolioSummary>;
  closeAllPositions(): Promise<PortfolioSummary>;
  getDecision(id: string): Promise<DecisionPacket>;
  getOrder(id: string): Promise<OrderResult>;
  approveDecision(id: string): Promise<OrderResult>;
  rejectDecision(id: string): Promise<{ success: boolean; decisionId: string }>;
  getVolSurface(underlying?: string): Promise<VolatilitySurface>;
  getAnomalies(underlying?: string): Promise<AnomalyReport[]>;
  getStrategyCandidates(underlying?: string, targetDelta?: number, budget?: number): Promise<StrategyCandidate[]>;
  getStressReport(strategyId?: string): Promise<StressReport>;
  getAgentTrace(decisionId?: string): Promise<AgentTraceStep[]>;
  getActiveOperation(): Promise<ActiveOperationState>;
  getHistoricalDecisions(): Promise<HistoricalDecisionSummary[]>;
  getCounterfactual(params?: Record<string, unknown>): Promise<CounterfactualComparison>;
  getSettings(): Promise<import('@/types/voltron').SystemSettings>;
  updateSettings(req: import('@/types/voltron').UpdateSettingsRequest): Promise<import('@/types/voltron').SystemSettings>;
  testLlmConnection(req: import('@/types/voltron').TestConnectionRequest): Promise<import('@/types/voltron').TestConnectionResponse>;
  dispatchMandate(
    mandate: string,
    onProgress?: (step: MandatePipelineStep) => void,
    autonomyLevel?: import('@/types/voltron').AutonomyLevel
  ): Promise<{ operationId: string; decisionId: string; packet: DecisionPacket }>;
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
      let msg = errorText;
      try {
        const parsed = JSON.parse(errorText);
        if (parsed.detail) {
          msg = parsed.detail;
        }
      } catch {}
      throw new Error(msg);
    }
    return res.json();
  }

  async getTelemetry(): Promise<TelemetryStatus> {
    return this.fetchJson<TelemetryStatus>('/telemetry');
  }

  async getPortfolio(): Promise<PortfolioSummary> {
    return this.fetchJson<PortfolioSummary>('/portfolio');
  }

  async rebalancePortfolio(): Promise<PortfolioSummary> {
    return this.fetchJson<PortfolioSummary>('/portfolio/rebalance', { method: 'POST' });
  }

  async closeAllPositions(): Promise<PortfolioSummary> {
    return this.fetchJson<PortfolioSummary>('/portfolio/close-all', { method: 'POST' });
  }

  async getPortfolioHistory(period: string = '1M', timeframe: string = '1D'): Promise<PortfolioHistory> {
    return this.fetchJson<PortfolioHistory>(`/portfolio/history?period=${period}&timeframe=${timeframe}`);
  }

  async getDecision(id: string): Promise<DecisionPacket> {
    return this.fetchJson<DecisionPacket>(`/decisions/${id}`);
  }

  async getOrder(id: string): Promise<OrderResult> {
    return this.fetchJson<OrderResult>(`/orders/${id}`);
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

  async getAnomalies(underlying: string = 'SPY'): Promise<AnomalyReport[]> {
    return this.fetchJson<AnomalyReport[]>(`/quant/anomalies?symbol=${underlying}`);
  }

  async getStrategyCandidates(
    underlying: string = 'SPY',
    targetDelta: number = 0.15,
    budget: number = 50000.0
  ): Promise<StrategyCandidate[]> {
    return this.fetchJson<StrategyCandidate[]>(
      `/quant/strategies?symbol=${underlying}&target_delta=${targetDelta}&budget=${budget}`
    );
  }

  async getStressReport(strategyId: string = 'strat-condor-01'): Promise<StressReport> {
    return this.fetchJson<StressReport>(`/quant/stress?strategy_id=${strategyId}`);
  }

  async getAgentTrace(decisionId: string = 'DEC-SPY-9942'): Promise<AgentTraceStep[]> {
    return this.fetchJson<AgentTraceStep[]>(`/quant/agents/trace/${decisionId}`);
  }

  async getActiveOperation(): Promise<ActiveOperationState> {
    return {
      operationId: 'OP-LIVE',
      mandate: 'Enter mandate to initiate live multi-agent options tournament on Alpaca Paper.',
      underlying: 'SPY',
      status: 'IDLE',
      currentStepIndex: 0,
      steps: [
        { id: 'step-1', title: '01. Researcher Agent: Market Regime', status: 'PENDING' },
        { id: 'step-2', title: '02. Volatility Analyst: Skew & Surface', status: 'PENDING' },
        { id: 'step-3', title: '03. Strategy Tournament: Lognormal POP', status: 'PENDING' },
        { id: 'step-4', title: '04. Critic Agent: Tail-Risk Scenarios', status: 'PENDING' },
        { id: 'step-5', title: '05. Deterministic Risk Compiler Gate', status: 'PENDING' },
        { id: 'step-6', title: '06. Alpaca Paper MLEG Dispatch', status: 'PENDING' },
      ],
    };
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

  async getSettings(): Promise<import('@/types/voltron').SystemSettings> {
    return this.fetchJson<import('@/types/voltron').SystemSettings>('/settings');
  }

  async updateSettings(req: import('@/types/voltron').UpdateSettingsRequest): Promise<import('@/types/voltron').SystemSettings> {
    return this.fetchJson<import('@/types/voltron').SystemSettings>('/settings', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  async testLlmConnection(req: import('@/types/voltron').TestConnectionRequest): Promise<import('@/types/voltron').TestConnectionResponse> {
    return this.fetchJson<import('@/types/voltron').TestConnectionResponse>('/settings/test', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  async dispatchMandate(
    mandate: string,
    onProgress?: (step: MandatePipelineStep) => void,
    autonomyLevel?: import('@/types/voltron').AutonomyLevel
  ): Promise<{ operationId: string; decisionId: string; packet: DecisionPacket }> {
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
                DATA_FETCH: 'step-1',
                RESEARCH: 'step-1',
                VOLATILITY: 'step-2',
                QUANT_GEN: 'step-3',
                STRATEGY: 'step-3',
                CRITIC: 'step-4',
                RISK: 'step-5',
                EXECUTION: 'step-6',
                DECISION: 'step-6',
                COMPLETE: 'step-6',
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
      // 1. Dynamically extract target ticker symbol from mandate for ANY stock
      const STOP_WORDS = new Set([
        'BUY', 'SELL', 'CALL', 'PUT', 'WITH', 'RISK', 'FOR', 'THE', 'SCAN', 'RUN', 'MODE',
        'AUTO', 'TRADE', 'DELTA', 'WING', 'SKEW', 'IRON', 'SPREAD', 'CONDOR', 'CREDIT',
        'DEBIT', 'HIGH', 'LOW', 'LONG', 'SHORT', 'AND', 'OUT', 'IN', 'TO', 'ON', 'FIND',
        'LOOK', 'OPEN', 'CLOSE', 'EXIT', 'STOP', 'LOSS', 'TARGET', 'MAX', 'MIN', 'RATE',
        'VOL', 'DAYS', 'DTE', 'CASH', 'BASKET', 'STOCK', 'STOCKS', 'OPTION', 'OPTIONS',
        'LEGS', 'LEG', 'ENTRY', 'MARK', 'TIME', 'PRICE', 'GAIN', 'WIN', 'DROP', 'SHOCK',
        'CRASH', 'AI', 'MCP', 'HARVEST', 'SEEK', 'BUILD', 'NEUTRAL', 'BETA', 'ANALYZE'
      ]);

      let targetSymbol = 'SPY';
      // Preposition search (e.g. 'on PLTR', 'for TSLA', 'symbol AMD')
      const prepMatch = mandate.match(/\b(?:on|for|in|stock|symbol|ticker|analyze|harvest|trade)\s+([A-Za-z]{1,6})\b/i);
      if (prepMatch && !STOP_WORDS.has(prepMatch[1].toUpperCase())) {
        targetSymbol = prepMatch[1].toUpperCase();
      } else {
        // Uppercase search
        const upperMatches = mandate.match(/\b[A-Z]{2,6}\b/g) || [];
        const validUpper = upperMatches.find((tok) => !STOP_WORDS.has(tok));
        if (validUpper) {
          targetSymbol = validUpper;
        } else {
          // Known high-liquidity symbols
          const knownList = ['PLTR', 'COIN', 'SMCI', 'AMD', 'NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'META', 'GOOGL', 'QQQ', 'IWM', 'SPY', 'ARM', 'DIS', 'NFLX', 'UBER', 'BABA', 'BA', 'GLD', 'TLT'];
          const foundKnown = knownList.find((k) => new RegExp(`\\b${k}\\b`, 'i').test(mandate));
          if (foundKnown) {
            targetSymbol = foundKnown;
          }
        }
      }

      // Submit mandate to FastAPI /api/scan endpoint
      const packet = await this.fetchJson<DecisionPacket>('/scan', {
        method: 'POST',
        body: JSON.stringify({
          mandate,
          underlying: targetSymbol,
          autonomyLevel: autonomyLevel,
        }),
      });

      // 2. Notify final progress completion
      if (onProgress) {
        onProgress({
          id: 'step-6',
          title: packet.status === 'APPROVED' ? 'Order Executed on Alpaca Paper' : 'Decision Ready for Approval',
          status: 'COMPLETE',
          outputSummary: [
            `Strategy: ${packet.strategy?.name || 'Selected Structure'}`,
            `Status: ${packet.status} | Mode: ${packet.autonomyLevel || 'GUARDED_AUTONOMOUS'}`,
          ],
        });
      }

      return {
        operationId: `OP-${packet.id}`,
        decisionId: packet.id,
        packet: packet,
      };
    } finally {
      if (eventSource) {
        eventSource.close();
      }
    }
  }
}

// Export strictly the LIVE HttpSseApiAdapter
export const api: ApiClient = new HttpSseApiAdapter();
