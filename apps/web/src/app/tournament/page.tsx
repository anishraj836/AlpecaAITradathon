'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { StrategyCandidate } from '@/types/voltron';

const QUICK_SYMBOLS = ['SPY', 'QQQ', 'NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'META', 'GOOGL', 'AMD', 'PLTR', 'COIN'];

export default function OpportunityScannerPage() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('SPY');
  const [customTickerInput, setCustomTickerInput] = useState<string>('');
  const [strategies, setStrategies] = useState<StrategyCandidate[]>([]);
  const [sortBy, setSortBy] = useState<'score' | 'pop'>('score');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const loadTournament = async (symbol: string) => {
    setIsLoading(true);
    try {
      const data = await api.getStrategyCandidates(symbol);
      if (data && data.length > 0) setStrategies(data);
    } catch (err) {
      console.warn('Failed to load tournament candidates:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTournament(selectedSymbol);
  }, [selectedSymbol]);

  const rankedCandidates = strategies.filter((s) => !s.rejectionReason);
  const rejectedCandidates = strategies.filter((s) => s.rejectionReason);

  const sortedCandidates = [...rankedCandidates].sort((a, b) => {
    return sortBy === 'score' ? b.score - a.score : b.pop - a.pop;
  });

  return (
    <div className="flex flex-col w-full h-full gap-container-gap pb-container-gap">
      {/* Header Area */}
      <div className="flex flex-col gap-margin-compact bg-surface-container rounded-sm p-panel-padding shadow-md border border-outline-variant/20">
        <div className="flex items-center justify-between">
          <h1 className="font-display-lg text-display-lg text-primary tracking-tighter uppercase font-bold">
            Opportunity Scanner (Strategy Tournament)
          </h1>
          <div className="flex items-center gap-3">
            {/* Custom Ticker Search Form */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (customTickerInput.trim()) {
                  const sym = customTickerInput.trim().toUpperCase();
                  setSelectedSymbol(sym);
                  setCustomTickerInput('');
                }
              }}
              className="flex items-center gap-1.5 bg-surface border border-outline-variant/40 focus-within:border-primary/60 rounded-sm px-2.5 py-1 transition-all shadow-inner"
            >
              <span className="material-symbols-outlined text-[14px] text-outline">search</span>
              <input
                type="text"
                placeholder="Ticker (e.g. PLTR, AMD)..."
                value={customTickerInput}
                onChange={(e) => setCustomTickerInput(e.target.value.toUpperCase())}
                className="bg-transparent text-xs font-mono text-on-surface uppercase w-36 outline-none placeholder:text-outline/60 font-bold"
              />
              <button
                type="submit"
                className="px-2 py-0.5 bg-primary text-on-primary hover:bg-primary-fixed-dim text-[10px] font-mono font-bold rounded-sm transition-colors"
              >
                SCAN
              </button>
            </form>

            {/* Quick Chips */}
            <div className="hidden xl:flex items-center gap-1 bg-surface p-0.5 border border-outline-variant/30 rounded-sm">
              {QUICK_SYMBOLS.slice(0, 6).map((sym) => (
                <button
                  key={sym}
                  type="button"
                  onClick={() => setSelectedSymbol(sym)}
                  className={`px-2 py-0.5 text-xs font-mono font-bold rounded-sm transition-all ${
                    selectedSymbol === sym
                      ? 'bg-primary text-on-primary shadow-sm'
                      : 'text-on-surface-variant hover:text-primary hover:bg-surface-container-high'
                  }`}
                >
                  {sym}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2 px-3 py-1 bg-surface-container-high border border-primary/20 rounded-sm">
              <span className={`w-2 h-2 rounded-full bg-primary ${isLoading ? 'animate-ping' : 'animate-pulse'}`} />
              <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-widest font-mono">
                {isLoading ? 'Simulating...' : 'Tournament Complete'}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4 font-mono">
          <span className="font-data-lg text-data-lg text-on-surface font-bold">
            {strategies.length} STRUCTURES EVALUATED
          </span>
          <span className="font-body-sm text-body-sm text-on-surface-variant font-sans">
            | Underlying: <span className="text-primary-fixed-dim font-mono font-bold">{selectedSymbol}</span> | Target: <span className="text-on-surface">Theta Decay / Defined Risk</span>
          </span>
        </div>
      </div>

      <div className="flex flex-row gap-container-gap h-full min-h-0">
        {/* Main Tournament Leaderboard (Left 2/3) */}
        <div className="flex flex-col flex-2 bg-surface-container rounded-sm shadow-md overflow-hidden min-w-0 border border-outline-variant/20 flex-[2]">
          <div className="p-panel-padding bg-surface-container-high border-b border-outline-variant/30 flex justify-between items-center">
            <h2 className="font-headline-md text-headline-md text-on-surface uppercase tracking-tight font-semibold">
              Top Ranked Strategy Candidates
            </h2>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setSortBy('score')}
                className={`px-3 py-1 text-label-xs font-label-xs rounded-sm uppercase tracking-wider transition-colors ${
                  sortBy === 'score'
                    ? 'bg-primary text-background font-bold'
                    : 'bg-transparent text-primary border border-primary/30 hover:bg-primary/10'
                }`}
              >
                Sort by Score
              </button>
              <button
                type="button"
                onClick={() => setSortBy('pop')}
                className={`px-3 py-1 text-label-xs font-label-xs rounded-sm uppercase tracking-wider transition-colors ${
                  sortBy === 'pop'
                    ? 'bg-primary text-background font-bold'
                    : 'bg-transparent text-primary border border-primary/30 hover:bg-primary/10'
                }`}
              >
                Sort by POP
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-margin-compact space-y-container-gap">
            {sortedCandidates.map((strat, idx) => {
              const isWinner = idx === 0;
              return (
                <div
                  key={strat.id}
                  className={`relative flex flex-col bg-surface-container-low border rounded-sm p-panel-padding group hover:bg-surface-container-highest transition-colors ${
                    isWinner ? 'border-primary/40' : 'border-outline-variant/20'
                  }`}
                >
                  <div
                    className={`absolute left-0 top-0 bottom-0 w-[2px] ${
                      isWinner ? 'bg-primary' : 'bg-secondary-container opacity-0 group-hover:opacity-100'
                    }`}
                  />
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-3">
                      <span className="font-display-lg text-display-lg text-primary opacity-50 font-mono">
                        0{idx + 1}
                      </span>
                      <div>
                        <h3 className="font-data-lg text-data-lg text-on-surface uppercase tracking-tight font-bold">
                          {strat.name}
                        </h3>
                        <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-widest block mt-1 font-mono">
                          {strat.dte} DTE | {strat.underlying}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-6 text-right">
                      <div className="flex flex-col">
                        <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-wider">
                          Quant Score
                        </span>
                        <span className="font-data-lg text-data-lg text-primary font-mono font-bold">
                          {strat.score.toFixed(1)}
                        </span>
                      </div>
                      <Link
                        href="/decision/DEC-SPY-9942"
                        className="px-4 py-2 bg-primary/10 text-primary border border-primary/30 rounded-sm font-data-md text-data-md hover:bg-primary/20 transition-colors uppercase tracking-wider font-mono font-semibold"
                      >
                        View Analysis
                      </Link>
                    </div>
                  </div>

                  <div className="grid grid-cols-4 gap-4 bg-background p-3 rounded-sm border border-outline-variant/20 font-mono">
                    <div className="flex flex-col">
                      <span className="font-label-xs text-label-xs text-outline uppercase tracking-wider mb-1 font-sans">
                        Max Risk
                      </span>
                      <span className="font-data-md text-data-md text-error font-bold">
                        ${strat.maxLoss.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex flex-col">
                      <span className="font-label-xs text-label-xs text-outline uppercase tracking-wider mb-1 font-sans">
                        Max Profit
                      </span>
                      <span className="font-data-md text-data-md text-primary-fixed-dim font-bold">
                        ${strat.maxProfit.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex flex-col">
                      <span className="font-label-xs text-label-xs text-outline uppercase tracking-wider mb-1 font-sans">
                        POP
                      </span>
                      <span className="font-data-md text-data-md text-on-surface font-bold">
                        {(strat.pop * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex flex-col">
                      <span className="font-label-xs text-label-xs text-outline uppercase tracking-wider mb-1 font-sans">
                        Liquidity Score
                      </span>
                      <span className="font-data-md text-data-md text-on-surface font-bold">
                        {strat.liquidityScore} / 100
                      </span>
                    </div>
                  </div>

                  {strat.legs.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-outline-variant/20 flex gap-3 text-data-sm font-data-sm text-on-surface-variant font-mono">
                      {strat.legs.map((leg) => (
                        <span
                          key={leg.id}
                          className={`px-2 py-0.5 rounded-sm ${
                            leg.side === 'BUY'
                              ? 'bg-primary-fixed-dim/10 text-primary-fixed-dim border border-primary-fixed-dim/20'
                              : 'bg-error/10 text-error border border-error/20'
                          }`}
                        >
                          {leg.side === 'BUY' ? '+1' : '-1'} {leg.underlying} {leg.strike}{' '}
                          {leg.type === 'CALL' ? 'C' : 'P'}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Rejected Candidates Audit Panel (Right 1/3) */}
        <div className="flex flex-col flex-1 bg-surface-container rounded-sm shadow-md overflow-hidden min-w-[300px] border border-outline-variant/20">
          <div className="p-panel-padding bg-surface-container-high border-b border-outline-variant/30 flex items-center gap-2">
            <span className="material-symbols-outlined text-error text-[20px]">delete_sweep</span>
            <h2 className="font-headline-md text-headline-md text-on-surface uppercase tracking-tight font-semibold">
              Rejected Candidates
            </h2>
          </div>

          <div className="flex-1 overflow-y-auto p-margin-compact space-y-container-gap bg-background/50">
            {rejectedCandidates.map((rej) => (
              <div
                key={rej.id}
                className="bg-surface-container-low border border-outline-variant/10 rounded-sm p-3 opacity-75"
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="font-data-md text-data-md text-on-surface line-through decoration-error/50 font-mono font-bold">
                    {rej.name}
                  </span>
                  <span className="font-label-xs text-label-xs text-outline font-mono">
                    Score: {rej.score.toFixed(1)}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-error font-mono text-xs">
                  <span className="material-symbols-outlined text-[16px]">warning</span>
                  <span>{rej.rejectionReason}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
