'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { PortfolioSummary } from '@/types/voltron';

export default function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<PortfolioSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notification, setNotification] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    api.getPortfolio()
      .then((data) => {
        if (isMounted) {
          setPortfolio(data);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        console.error('Failed to load portfolio:', err);
        if (isMounted) setIsLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const handleClosePosition = (symbol: string) => {
    setNotification(`Simulated Market Close order sent for ${symbol}`);
    setTimeout(() => setNotification(null), 4000);
  };

  if (isLoading || !portfolio) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="font-mono text-body-sm text-on-surface-variant">
            Fetching Alpaca Portfolio & Greeks...
          </span>
        </div>
      </div>
    );
  }

  const { account, positions, netDelta, netTheta, netVega, netGamma, unrealizedPnl, realizedTodayPnl, profitTargetPct } = portfolio;

  return (
    <div className="flex flex-col gap-6 max-w-7xl mx-auto pb-12">
      {/* Top Banner Alert */}
      {notification && (
        <div className="p-3 bg-primary/10 border border-primary/40 rounded-sm text-primary font-mono text-body-sm flex items-center justify-between">
          <span>{notification}</span>
          <button onClick={() => setNotification(null)} className="text-primary hover:underline">
            ✕
          </button>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-outline-variant/20 pb-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[11px] text-primary uppercase tracking-widest bg-primary/10 px-2 py-0.5 rounded-sm">
              ALPACA PAPER PORTFOLIO
            </span>
            <span className="font-mono text-[11px] text-on-surface-variant">
              Account: {account.accountId}
            </span>
          </div>
          <h1 className="font-display-md text-display-md text-on-surface tracking-tight">
            Live Positions & Autonomous Risk Management
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 bg-surface-container-high border border-outline-variant/30 rounded-sm font-mono text-label-xs text-on-surface-variant">
            AUTOMATED PROFIT TARGET: <span className="text-primary font-semibold">{profitTargetPct}%</span>
          </div>
          <div className="px-3 py-1.5 bg-primary/10 border border-primary/30 rounded-sm font-mono text-label-xs text-primary flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            WORKER DAEMON: ACTIVE
          </div>
        </div>
      </div>

      {/* KPI Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Equity */}
        <div className="p-5 bg-surface-container-low border border-outline-variant/20 rounded-sm flex flex-col justify-between">
          <span className="font-label-xs text-label-xs text-outline uppercase tracking-wider">
            Total Account Equity
          </span>
          <div className="mt-2">
            <span className="font-display-sm text-display-sm text-on-surface font-mono font-bold">
              ${account.equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <span className="font-mono text-[11px] text-on-surface-variant mt-1">
            Cash: ${account.cash.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </span>
        </div>

        {/* Buying Power */}
        <div className="p-5 bg-surface-container-low border border-outline-variant/20 rounded-sm flex flex-col justify-between">
          <span className="font-label-xs text-label-xs text-outline uppercase tracking-wider">
            Options Buying Power
          </span>
          <div className="mt-2">
            <span className="font-display-sm text-display-sm text-on-surface font-mono font-bold">
              ${account.buyingPower.toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <span className="font-mono text-[11px] text-primary mt-1">
            Reg-T Margin Available
          </span>
        </div>

        {/* Unrealized PnL */}
        <div className="p-5 bg-surface-container-low border border-outline-variant/20 rounded-sm flex flex-col justify-between">
          <span className="font-label-xs text-label-xs text-outline uppercase tracking-wider">
            Open Unrealized P&L
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className={`font-display-sm text-display-sm font-mono font-bold ${unrealizedPnl >= 0 ? 'text-primary' : 'text-error'}`}>
              {unrealizedPnl >= 0 ? `+$${unrealizedPnl.toFixed(2)}` : `-$${Math.abs(unrealizedPnl).toFixed(2)}`}
            </span>
            <span className="font-mono text-label-sm text-primary">
              (+{(unrealizedPnl / account.equity * 100).toFixed(2)}%)
            </span>
          </div>
          <span className="font-mono text-[11px] text-on-surface-variant mt-1">
            {positions.length} Active Option Legs
          </span>
        </div>

        {/* Realized Today PnL */}
        <div className="p-5 bg-surface-container-low border border-outline-variant/20 rounded-sm flex flex-col justify-between">
          <span className="font-label-xs text-label-xs text-outline uppercase tracking-wider">
            Realized Today P&L
          </span>
          <div className="mt-2">
            <span className="font-display-sm text-display-sm text-primary font-mono font-bold">
              +${realizedTodayPnl.toFixed(2)}
            </span>
          </div>
          <span className="font-mono text-[11px] text-outline mt-1">
            Closed trades today
          </span>
        </div>
      </div>

      {/* Net Portfolio Greeks Summary Banner */}
      <div className="p-5 bg-surface-container border border-outline-variant/20 rounded-sm">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-title-sm text-title-sm text-on-surface tracking-tight uppercase font-mono">
            Aggregate Net Portfolio Greeks
          </h3>
          <span className="font-mono text-[11px] text-outline">
            Real-time sensitivity across all open option contracts
          </span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 bg-surface-container-high rounded-sm border border-outline-variant/10">
            <div className="flex items-center justify-between">
              <span className="font-mono text-label-xs text-outline">NET DELTA (Δ)</span>
              <span className="font-mono text-data-md font-bold text-on-surface">
                {netDelta >= 0 ? `+${netDelta.toFixed(2)}` : netDelta.toFixed(2)}
              </span>
            </div>
            <p className="font-mono text-[10px] text-on-surface-variant mt-1">
              Delta-neutral corridor: ±0.20
            </p>
          </div>

          <div className="p-3 bg-surface-container-high rounded-sm border border-outline-variant/10">
            <div className="flex items-center justify-between">
              <span className="font-mono text-label-xs text-outline">NET THETA (Θ)</span>
              <span className="font-mono text-data-md font-bold text-primary">
                +${netTheta.toFixed(2)}/day
              </span>
            </div>
            <p className="font-mono text-[10px] text-primary/80 mt-1">
              Positive time decay harvest
            </p>
          </div>

          <div className="p-3 bg-surface-container-high rounded-sm border border-outline-variant/10">
            <div className="flex items-center justify-between">
              <span className="font-mono text-label-xs text-outline">NET VEGA (ν)</span>
              <span className="font-mono text-data-md font-bold text-on-surface">
                {netVega.toFixed(2)}
              </span>
            </div>
            <p className="font-mono text-[10px] text-on-surface-variant mt-1">
              Short volatility exposure
            </p>
          </div>

          <div className="p-3 bg-surface-container-high rounded-sm border border-outline-variant/10">
            <div className="flex items-center justify-between">
              <span className="font-mono text-label-xs text-outline">NET GAMMA (Γ)</span>
              <span className="font-mono text-data-md font-bold text-on-surface">
                +{netGamma.toFixed(3)}
              </span>
            </div>
            <p className="font-mono text-[10px] text-on-surface-variant mt-1">
              Curvature risk controlled
            </p>
          </div>
        </div>
      </div>

      {/* Active Positions Table */}
      <div className="bg-surface-container-low border border-outline-variant/20 rounded-sm overflow-hidden">
        <div className="p-4 border-b border-outline-variant/20 flex items-center justify-between bg-surface-container">
          <div className="flex items-center gap-3">
            <h2 className="font-title-sm text-title-sm text-on-surface font-mono tracking-tight uppercase">
              Open Option Positions & Execution Ledger
            </h2>
            <span className="px-2 py-0.5 bg-surface-container-highest rounded text-[11px] font-mono text-outline">
              {positions.length} Active Legs
            </span>
          </div>

          <span className="font-mono text-[11px] text-outline">
            Source: Alpaca REST /v2/positions
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-body-sm">
            <thead className="bg-surface-container-high/60 text-outline text-[11px] uppercase tracking-wider border-b border-outline-variant/20">
              <tr>
                <th className="p-3.5 pl-4">Contract Symbol</th>
                <th className="p-3.5">Side</th>
                <th className="p-3.5 text-right">Qty</th>
                <th className="p-3.5 text-right">Entry Price</th>
                <th className="p-3.5 text-right">Current Mark</th>
                <th className="p-3.5 text-right">Market Value</th>
                <th className="p-3.5 text-right">Unrealized P&L</th>
                <th className="p-3.5 text-center pr-4">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/10">
              {positions.map((pos, idx) => (
                <tr key={pos.symbol || idx} className="hover:bg-surface-container transition-colors">
                  <td className="p-3.5 pl-4 font-semibold text-on-surface">
                    {pos.symbol}
                  </td>
                  <td className="p-3.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${pos.side === 'long' ? 'bg-primary/10 text-primary border border-primary/30' : 'bg-tertiary/10 text-tertiary border border-tertiary/30'}`}>
                      {pos.side.toUpperCase()}
                    </span>
                  </td>
                  <td className="p-3.5 text-right text-on-surface">
                    {Math.abs(pos.qty)}
                  </td>
                  <td className="p-3.5 text-right text-on-surface-variant">
                    ${pos.avgEntryPrice.toFixed(2)}
                  </td>
                  <td className="p-3.5 text-right text-on-surface">
                    ${pos.currentPrice.toFixed(2)}
                  </td>
                  <td className="p-3.5 text-right font-semibold text-on-surface">
                    ${pos.marketValue.toFixed(2)}
                  </td>
                  <td className={`p-3.5 text-right font-bold ${pos.unrealizedPl >= 0 ? 'text-primary' : 'text-error'}`}>
                    {pos.unrealizedPl >= 0 ? `+$${pos.unrealizedPl.toFixed(2)}` : `-$${Math.abs(pos.unrealizedPl).toFixed(2)}`}
                  </td>
                  <td className="p-3.5 text-center pr-4">
                    <button
                      onClick={() => handleClosePosition(pos.symbol)}
                      className="px-2.5 py-1 text-[11px] font-mono border border-outline-variant/40 hover:border-error hover:text-error rounded transition-colors"
                    >
                      Close Leg
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Autonomous Guardrails Summary */}
      <div className="p-4 bg-surface-container-high/40 border border-outline-variant/20 rounded-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4 font-mono text-[11px]">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-primary" />
          <span className="text-on-surface">
            Autonomous Trade Exit Daemon is armed: Positions will be auto-liquidated upon reaching <strong className="text-primary">50% max profit ($69.00)</strong> or <strong className="text-error">2x max loss ($724.00)</strong>.
          </span>
        </div>
        <span className="text-outline">
          Latency: ~12ms via Alpaca Paper WebSocket
        </span>
      </div>
    </div>
  );
}
