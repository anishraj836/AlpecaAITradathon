'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { StressReport } from '@/types/voltron';
import { DEMO_STRESS_REPORT } from '@/fixtures/voltronFixtures';

export default function PayoffStressLabPage() {
  const [stressReport, setStressReport] = useState<StressReport>(DEMO_STRESS_REPORT);
  const [riskBudget, setRiskBudget] = useState('$50,000');
  const [targetDelta, setTargetDelta] = useState('+0.15 β');
  const [horizon, setHorizon] = useState('45 Days');
  const [isSimulating, setIsSimulating] = useState(false);

  useEffect(() => {
    let isMounted = true;
    api.getStressReport().then((data) => {
      if (isMounted) setStressReport(data);
    });
    return () => {
      isMounted = false;
    };
  }, []);

  const handleRerun = async () => {
    setIsSimulating(true);
    try {
      const refreshed = await api.getStressReport(stressReport.strategyId);
      setStressReport(refreshed);
    } finally {
      setTimeout(() => setIsSimulating(false), 500);
    }
  };

  // Group matrix cells by price shift
  const priceShifts = [3.0, 1.5, 0.0, -1.5, -3.0];
  const ivShifts = [-20, 0, 20];

  const getCellPnl = (priceShift: number, ivShift: number) => {
    const found = stressReport.matrix.find(
      (m) => m.priceShiftPct === priceShift && m.ivShiftPct === ivShift
    );
    return found ? found.pnl : 0;
  };

  return (
    <div className="flex flex-col w-full gap-container-gap pb-container-gap">
      {/* Top Context Bar */}
      <div className="flex items-center justify-between p-panel-padding bg-surface-container relative overflow-hidden group rounded-sm border border-outline-variant/20">
        <div className="flex items-center gap-4 relative z-10">
          <span className="material-symbols-outlined text-primary">science</span>
          <h2 className="font-headline-md text-headline-md text-on-surface tracking-widest uppercase m-0 font-semibold">
            Payoff &amp; Stress Lab (Scenario Analysis)
          </h2>
        </div>
        <div className="flex gap-4 items-center relative z-10">
          <div className="flex flex-col items-end">
            <span className="font-label-xs text-label-xs text-outline uppercase tracking-widest">
              Active Model
            </span>
            <span className="font-data-md text-data-md text-primary-fixed-dim font-mono font-bold">
              {stressReport.modelId}
            </span>
          </div>
          <div className="w-px h-8 bg-outline-variant/30" />
          <div className="px-3 py-1.5 bg-surface-container-low text-on-surface-variant font-data-sm text-data-sm uppercase tracking-widest flex items-center gap-2 border border-outline-variant/30 font-mono">
            <div className="w-1.5 h-1.5 bg-tertiary-container animate-pulse rounded-full" />
            Simulation Live
          </div>
        </div>
      </div>

      {/* Main Workspace Split */}
      <div className="flex flex-col xl:flex-row w-full gap-container-gap flex-1 min-h-0">
        {/* Sidebar Controls */}
        <div className="w-full xl:w-80 flex flex-col gap-container-gap shrink-0">
          <div className="flex flex-col p-panel-padding bg-surface-container h-full relative rounded-sm border border-outline-variant/20">
            <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-outline-variant/50" />
            <div className="mb-6">
              <h3 className="font-label-xs text-label-xs text-outline uppercase tracking-widest">
                Model Assumptions
              </h3>
            </div>

            <div className="flex flex-col gap-5 flex-1 font-mono">
              <div className="flex flex-col gap-1.5">
                <label className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-wider flex justify-between font-sans">
                  <span>Risk Budget</span>
                  <span className="text-outline">Max DD</span>
                </label>
                <input
                  type="text"
                  value={riskBudget}
                  onChange={(e) => setRiskBudget(e.target.value)}
                  className="w-full bg-background text-on-surface font-data-md text-data-md p-3 outline-none border border-outline-variant/30 focus:border-primary/50 transition-all rounded-sm"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-wider font-sans">
                  Target Portfolio Delta
                </label>
                <input
                  type="text"
                  value={targetDelta}
                  onChange={(e) => setTargetDelta(e.target.value)}
                  className="w-full bg-background text-primary-fixed-dim font-data-md text-data-md p-3 outline-none border border-outline-variant/30 focus:border-primary/50 transition-all rounded-sm"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-wider font-sans">
                  Evaluation Horizon
                </label>
                <input
                  type="text"
                  value={horizon}
                  onChange={(e) => setHorizon(e.target.value)}
                  className="w-full bg-background text-on-surface font-data-md text-data-md p-3 outline-none border border-outline-variant/30 focus:border-primary/50 transition-all rounded-sm"
                />
              </div>

              <div className="flex flex-col gap-2 mt-4 pt-4 border-t border-outline-variant/30">
                <div className="flex justify-between items-center">
                  <span className="font-label-xs text-label-xs text-outline uppercase tracking-widest font-sans">
                    Implied Vol Regime
                  </span>
                  <span className="font-data-sm text-data-sm text-tertiary-container bg-tertiary-container/10 px-1.5 py-0.5 rounded-sm">
                    {stressReport.assumptions.volRegime}
                  </span>
                </div>
                <div className="h-1.5 bg-background w-full relative overflow-hidden border border-outline-variant/30">
                  <div className="absolute left-0 top-0 bottom-0 w-[85%] bg-tertiary-container/80" />
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={handleRerun}
              disabled={isSimulating}
              className="mt-6 w-full bg-primary text-on-primary font-data-md text-data-md py-3.5 uppercase tracking-wider hover:bg-primary-fixed-dim transition-all flex items-center justify-center gap-3 rounded-sm font-bold shadow-glow-primary"
            >
              <span className={`material-symbols-outlined text-[20px] ${isSimulating ? 'animate-spin' : ''}`}>
                sync
              </span>
              {isSimulating ? 'Re-running...' : 'Re-run Tournament'}
            </button>
          </div>
        </div>

        {/* Main Data Area */}
        <div className="flex flex-col flex-1 gap-container-gap min-w-0">
          {/* Payoff Chart Panel */}
          <div className="flex flex-col p-panel-padding bg-surface-container relative min-h-[300px] flex-1 rounded-sm border border-outline-variant/20">
            <div className="flex justify-between items-start mb-3 z-10 relative">
              <div className="flex flex-col">
                <h3 className="font-label-xs text-label-xs text-outline uppercase tracking-widest">
                  Estimated Payoff Profile (T+0 vs Expiration)
                </h3>
                <span className="font-data-lg text-data-lg text-on-surface mt-1 font-bold">
                  Multi-Leg Iron Condor Variant
                </span>
              </div>
              <div className="flex gap-6 bg-surface-container-low px-3 py-1.5 border border-outline-variant/30 rounded-sm font-mono text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-0.5 bg-primary shadow-glow-primary" />
                  <span className="text-on-surface-variant">T+0 Curve</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-0.5 border-dashed border-t border-tertiary-container" />
                  <span className="text-on-surface-variant">Expiration</span>
                </div>
              </div>
            </div>

            <div className="flex-1 w-full relative min-h-[180px]">
              <svg className="w-full h-full absolute inset-0" viewBox="0 0 1000 300" preserveAspectRatio="none">
                {/* Grid */}
                <line x1="0" y1="150" x2="1000" y2="150" stroke="#3b494c" strokeDasharray="4 4" strokeWidth="1" />
                <line x1="500" y1="0" x2="500" y2="300" stroke="#5203d5" strokeWidth="1.5" />
                {/* Expiration Curve */}
                <path
                  d="M0,260 L200,260 L350,60 L650,60 L800,260 L1000,260"
                  fill="none"
                  stroke="#fec931"
                  strokeDasharray="6 4"
                  strokeWidth="2"
                  opacity="0.8"
                />
                {/* T+0 Curve */}
                <path
                  d="M0,220 Q200,220 300,150 Q350,90 500,90 Q650,90 700,150 Q800,220 1000,220"
                  fill="none"
                  stroke="#c3f5ff"
                  strokeWidth="3"
                />
                <circle cx="300" cy="150" r="4" fill="#0d1516" stroke="#c3f5ff" strokeWidth="2" />
                <circle cx="700" cy="150" r="4" fill="#0d1516" stroke="#c3f5ff" strokeWidth="2" />
              </svg>

              {/* Profit Zone Box */}
              <div className="absolute top-4 left-[52%] bg-surface-container-high border border-primary/30 p-3 shadow-xl backdrop-blur-sm z-10 min-w-[140px] rounded-sm font-mono">
                <div className="font-label-xs text-label-xs text-outline uppercase mb-1 font-sans">
                  Max Profit Zone
                </div>
                <div className="font-data-lg text-data-lg text-primary font-bold">
                  +${stressReport.maxProfitZone.maxPnl.toLocaleString()}
                </div>
                <div className="w-full h-px bg-outline-variant/30 my-1.5" />
                <div className="font-data-sm text-data-sm text-on-surface-variant flex justify-between">
                  <span>SPY Corridor</span>
                  <span className="text-on-surface font-bold">
                    {stressReport.maxProfitZone.minPrice} - {stressReport.maxProfitZone.maxPrice}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Stress Matrix Panel */}
          <div className="flex flex-col p-panel-padding bg-surface-container relative flex-1 rounded-sm border border-outline-variant/20">
            <div className="flex justify-between items-end mb-3 z-10 relative">
              <h3 className="font-label-xs text-label-xs text-outline uppercase tracking-widest m-0">
                Scenario Analysis: Price vs Volatility Stress Matrix
              </h3>
              <div className="flex items-center gap-4 bg-background px-2.5 py-1 border border-outline-variant/20 rounded-sm font-mono text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 bg-primary rounded-none" />
                  <span className="text-on-surface-variant">Profit</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 bg-error rounded-none" />
                  <span className="text-on-surface-variant">Loss</span>
                </div>
              </div>
            </div>

            {/* Scenario Matrix Table */}
            <div className="w-full h-full bg-outline-variant/30 flex flex-col gap-gutter border border-outline-variant/30 overflow-hidden relative rounded-sm font-mono">
              {/* Header */}
              <div className="grid grid-cols-4 gap-gutter bg-outline-variant/30 shrink-0">
                <div className="bg-surface-container-low p-2 flex items-center justify-center font-label-xs text-label-xs text-on-surface-variant uppercase tracking-widest">
                  SPY Shift
                </div>
                <div className="bg-surface-container-low p-2 flex items-center justify-center font-label-xs text-label-xs text-on-surface-variant uppercase tracking-widest">
                  IV -20%
                </div>
                <div className="bg-surface-container-low p-2 flex items-center justify-center font-label-xs text-label-xs text-primary-fixed uppercase tracking-widest border-t-2 border-secondary-container">
                  Current Vol
                </div>
                <div className="bg-surface-container-low p-2 flex items-center justify-center font-label-xs text-label-xs text-on-surface-variant uppercase tracking-widest">
                  IV +20%
                </div>
              </div>

              {/* Rows */}
              {priceShifts.map((priceShift) => {
                const isZero = priceShift === 0.0;
                return (
                  <div
                    key={priceShift}
                    className={`grid grid-cols-4 gap-gutter bg-outline-variant/30 flex-1 min-h-[36px] ${
                      isZero ? 'relative border-y border-secondary-container/50' : ''
                    }`}
                  >
                    <div
                      className={`p-2 flex items-center justify-end pr-4 ${
                        isZero ? 'bg-surface-container-high text-secondary-fixed font-bold' : 'bg-surface-container text-on-surface'
                      }`}
                    >
                      {priceShift > 0 ? `+${priceShift.toFixed(1)}%` : `${priceShift.toFixed(1)}%`}
                    </div>

                    {ivShifts.map((ivShift) => {
                      const pnl = getCellPnl(priceShift, ivShift);
                      const isProfit = pnl >= 0;
                      return (
                        <div
                          key={ivShift}
                          className={`p-2 flex items-center justify-end pr-4 transition-colors cursor-crosshair ${
                            isProfit
                              ? 'bg-primary/10 text-primary hover:bg-primary/20 font-bold'
                              : 'bg-error/10 text-error hover:bg-error/20'
                          }`}
                        >
                          {isProfit ? `+$${pnl.toLocaleString()}` : `-$${Math.abs(pnl).toLocaleString()}`}
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
