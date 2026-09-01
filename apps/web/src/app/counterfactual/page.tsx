'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { CounterfactualComparison } from '@/types/voltron';

export default function CounterfactualLabPage() {
  const [data, setData] = useState<CounterfactualComparison | null>(null);
  const [targetDelta, setTargetDelta] = useState<number>(15);
  const [dteDays, setDteDays] = useState<number>(30);
  const [budget, setBudget] = useState<number>(2500);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    let isMounted = true;
    api.getCounterfactual().then((res) => {
      if (isMounted) setData(res);
    });
    return () => {
      isMounted = false;
    };
  }, []);

  const handleRunSimulation = async () => {
    setIsRunning(true);
    try {
      const res = await api.getCounterfactual({ targetDelta, dteDays, budget });
      setData(res);
    } finally {
      setTimeout(() => setIsRunning(false), 500);
    }
  };

  if (!data || !data.baseline || !data.scenario) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] gap-3">
        <span className="material-symbols-outlined text-[42px] text-primary animate-spin">refresh</span>
        <p className="font-mono text-sm text-on-surface font-bold">Computing Quantitative Counterfactual Sensitivity...</p>
        <p className="font-mono text-xs text-outline">Solving closed-form Black-Scholes and Acklam inverse-CDF strikes</p>
      </div>
    );
  }

  const { baseline, scenario } = data;

  return (
    <div className="flex flex-col w-full h-full pb-container-gap">
      {/* Top Banner */}
      <div className="flex items-center justify-between mb-4 mt-2 px-1">
        <div className="flex flex-col gap-1">
          <h1 className="font-display-lg text-display-lg text-primary tracking-tighter font-bold uppercase">
            What Would Change The Decision?
          </h1>
          <span className="font-data-md text-data-md text-on-surface-variant uppercase tracking-widest font-mono">
            Simulation Engine Active · Exploring Parameter Thresholds
          </span>
        </div>
        <div className="flex gap-2 font-mono">
          <button
            type="button"
            className="px-4 py-2 border border-primary text-primary hover:bg-primary/10 transition-colors font-data-md text-data-md rounded-none flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-[18px]">save</span>
            SAVE SCENARIO
          </button>
          <button
            type="button"
            onClick={handleRunSimulation}
            disabled={isRunning}
            className="px-4 py-2 bg-primary text-on-primary hover:bg-primary-fixed-dim transition-colors font-data-md text-data-md rounded-none flex items-center gap-2 font-bold shadow-glow-primary"
          >
            <span className={`material-symbols-outlined text-[18px] ${isRunning ? 'animate-spin' : ''}`}>
              play_arrow
            </span>
            {isRunning ? 'SIMULATING...' : 'RUN SIMULATION'}
          </button>
        </div>
      </div>

      {/* Split Comparison Panes */}
      <div className="grid grid-cols-2 gap-[1px] bg-outline-variant/30 w-full flex-1 min-h-[520px] border border-outline-variant/30 shadow-lg rounded-sm overflow-hidden">
        {/* Left Pane: Current Assumptions (Baseline) */}
        <div className="bg-surface-container flex flex-col relative h-full">
          <div className="h-10 border-b border-outline-variant/30 flex items-center px-4 bg-surface-container-high justify-between">
            <span className="font-data-lg text-data-lg text-on-surface flex items-center gap-2 font-mono font-bold">
              <div className="w-2 h-2 rounded-full bg-outline" />
              CURRENT ASSUMPTIONS
            </span>
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase bg-surface px-2 py-0.5 border border-outline-variant/30 font-mono">
              Baseline
            </span>
          </div>

          <div className="p-6 flex-1 overflow-y-auto flex flex-col gap-6 font-mono">
            {/* Parameters Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="border border-outline-variant/30 bg-surface p-4 flex flex-col relative group">
                <span className="font-label-xs text-label-xs text-on-surface-variant mb-1 font-sans">
                  TARGET DELTA
                </span>
                <span className="font-display-lg text-display-lg text-primary-fixed-dim font-bold">
                  {baseline.targetDelta}
                </span>
              </div>
              <div className="border border-outline-variant/30 bg-surface p-4 flex flex-col relative group">
                <span className="font-label-xs text-label-xs text-on-surface-variant mb-1 font-sans">
                  DTE (DAYS TO EXP)
                </span>
                <span className="font-display-lg text-display-lg text-on-surface font-bold">
                  {baseline.dteDays}D
                </span>
              </div>
              <div className="border border-outline-variant/30 bg-surface p-4 flex flex-col relative group col-span-2">
                <span className="font-label-xs text-label-xs text-on-surface-variant mb-1 font-sans">
                  ALLOCATED BUDGET
                </span>
                <span className="font-display-lg text-display-lg text-tertiary-container font-bold">
                  ${baseline.allocatedBudget.toLocaleString()}.00
                </span>
              </div>
            </div>

            {/* Current Winner */}
            <div className="flex flex-col gap-3">
              <span className="font-label-xs text-label-xs text-outline tracking-widest uppercase border-b border-outline-variant/30 pb-2 font-sans">
                BASELINE WINNER
              </span>
              <div className="border border-outline-variant/30 bg-surface-container-low p-5 relative overflow-hidden rounded-sm">
                <div className="flex justify-between items-start mb-4 relative z-10">
                  <div className="flex flex-col gap-1">
                    <span className="font-data-lg text-data-lg text-primary font-bold">
                      {baseline.winningStrategy.name}
                    </span>
                    <span className="font-data-md text-data-md text-on-surface-variant">
                      SPY 625/630 - 660/665
                    </span>
                  </div>
                  <div className="bg-primary-container text-on-primary-container px-2 py-1 font-label-xs text-label-xs font-bold">
                    SCORE: {baseline.winningStrategy.score.toFixed(1)}
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 mt-4 relative z-10">
                  <div className="flex flex-col p-2 bg-surface">
                    <span className="font-label-xs text-label-xs text-on-surface-variant font-sans">
                      MAX PROFIT
                    </span>
                    <span className="font-data-md text-data-md text-primary-fixed-dim font-bold">
                      ${baseline.winningStrategy.maxProfit}
                    </span>
                  </div>
                  <div className="flex flex-col p-2 bg-surface">
                    <span className="font-label-xs text-label-xs text-on-surface-variant font-sans">
                      MAX LOSS
                    </span>
                    <span className="font-data-md text-data-md text-error font-bold">
                      -${baseline.winningStrategy.maxLoss}
                    </span>
                  </div>
                  <div className="flex flex-col p-2 bg-surface">
                    <span className="font-label-xs text-label-xs text-on-surface-variant font-sans">
                      POP
                    </span>
                    <span className="font-data-md text-data-md text-on-surface font-bold">
                      {(baseline.winningStrategy.pop * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Pane: Modified Assumptions (Scenario A) */}
        <div className="bg-surface-container flex flex-col relative h-full">
          <div className="h-10 border-b border-outline-variant/30 flex items-center px-4 bg-surface-container-highest justify-between relative z-10">
            <span className="font-data-lg text-data-lg text-primary flex items-center gap-2 font-mono font-bold">
              <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              MODIFIED ASSUMPTIONS
            </span>
            <span className="font-label-xs text-label-xs text-on-tertiary-container uppercase bg-tertiary-container px-2 py-0.5 border border-tertiary/50 font-mono font-bold">
              Scenario A
            </span>
          </div>

          <div className="p-6 flex-1 overflow-y-auto flex flex-col gap-6 relative z-10 font-mono">
            {/* Tunable Parameters Grid */}
            <div className="grid grid-cols-2 gap-4">
              <div className="border border-primary/40 bg-surface-container-low p-4 flex flex-col relative group shadow-glow-primary rounded-sm">
                <div className="absolute -top-2 -right-2 bg-primary text-on-primary font-label-xs text-label-xs px-1 py-0.5 font-bold">
                  MOD
                </div>
                <span className="font-label-xs text-label-xs text-on-surface-variant mb-1 font-sans">
                  TARGET DELTA
                </span>
                <div className="flex items-end justify-between gap-2 mb-2">
                  <span className="font-display-lg text-display-lg text-primary font-bold">
                    {targetDelta}
                  </span>
                  <span className="font-data-sm text-data-sm text-error mb-2 flex items-center">
                    <span className="material-symbols-outlined text-[14px]">arrow_downward</span>
                    {(baseline.targetDelta - targetDelta).toFixed(0)}
                  </span>
                </div>
                <input
                  type="range"
                  min="5"
                  max="40"
                  step="1"
                  value={targetDelta}
                  onChange={(e) => setTargetDelta(Number(e.target.value))}
                  className="w-full accent-primary cursor-pointer"
                />
              </div>

              <div className="border border-primary/40 bg-surface-container-low p-4 flex flex-col relative group shadow-glow-primary rounded-sm">
                <div className="absolute -top-2 -right-2 bg-primary text-on-primary font-label-xs text-label-xs px-1 py-0.5 font-bold">
                  MOD
                </div>
                <span className="font-label-xs text-label-xs text-on-surface-variant mb-1 font-sans">
                  DTE (DAYS TO EXP)
                </span>
                <div className="flex items-end justify-between gap-2 mb-2">
                  <span className="font-display-lg text-display-lg text-on-surface font-bold">
                    {dteDays}D
                  </span>
                  <span className="font-data-sm text-data-sm text-error mb-2 flex items-center">
                    <span className="material-symbols-outlined text-[14px]">arrow_downward</span>
                    {baseline.dteDays - dteDays}D
                  </span>
                </div>
                <input
                  type="range"
                  min="7"
                  max="90"
                  step="1"
                  value={dteDays}
                  onChange={(e) => setDteDays(Number(e.target.value))}
                  className="w-full accent-primary cursor-pointer"
                />
              </div>

              <div className="border border-tertiary-container/50 bg-surface-container-low p-4 flex flex-col relative group col-span-2 shadow-glow-tertiary rounded-sm">
                <div className="absolute -top-2 -right-2 bg-tertiary-container text-on-tertiary-container font-label-xs text-label-xs px-1 py-0.5 font-bold">
                  MOD
                </div>
                <span className="font-label-xs text-label-xs text-on-surface-variant mb-1 font-sans">
                  ALLOCATED BUDGET
                </span>
                <div className="flex items-end justify-between gap-2 mb-2">
                  <span className="font-display-lg text-display-lg text-tertiary-container font-bold">
                    ${budget.toLocaleString()}.00
                  </span>
                  <span className="font-data-sm text-data-sm text-primary-fixed-dim mb-2 flex items-center">
                    <span className="material-symbols-outlined text-[14px]">arrow_upward</span>
                    +${(budget - baseline.allocatedBudget).toLocaleString()}
                  </span>
                </div>
                <input
                  type="range"
                  min="500"
                  max="10000"
                  step="250"
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                  className="w-full accent-tertiary cursor-pointer"
                />
              </div>
            </div>

            {/* Scenario Winner */}
            <div className="flex flex-col gap-3">
              <span className="font-label-xs text-label-xs text-outline tracking-widest uppercase border-b border-outline-variant/30 pb-2 font-sans">
                SCENARIO WINNER
              </span>
              <div className="border border-tertiary-container/30 bg-surface-container-highest p-5 relative overflow-hidden rounded-sm">
                <div className="flex justify-between items-start mb-4 relative z-10">
                  <div className="flex flex-col gap-1">
                    <span className="font-data-lg text-data-lg text-tertiary-container font-bold">
                      {scenario.winningStrategy.name}
                    </span>
                    <span className="font-data-md text-data-md text-on-surface-variant">
                      SPY 620/628 - 662/670 (Wide Wings)
                    </span>
                  </div>
                  <div className="bg-tertiary-container text-on-tertiary-container px-2 py-1 font-label-xs text-label-xs font-bold">
                    SCORE: {scenario.winningStrategy.score.toFixed(1)}
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 mt-4 relative z-10">
                  <div className="flex flex-col p-2 bg-surface border border-outline-variant/20">
                    <span className="font-label-xs text-label-xs text-on-surface-variant font-sans">
                      MAX PROFIT
                    </span>
                    <span className="font-data-md text-data-md text-primary-fixed-dim font-bold">
                      ${scenario.winningStrategy.maxProfit}
                    </span>
                  </div>
                  <div className="flex flex-col p-2 bg-surface border border-outline-variant/20">
                    <span className="font-label-xs text-label-xs text-on-surface-variant font-sans">
                      MAX LOSS
                    </span>
                    <span className="font-data-md text-data-md text-error font-bold">
                      -${scenario.winningStrategy.maxLoss}
                    </span>
                  </div>
                  <div className="flex flex-col p-2 bg-surface border border-outline-variant/20">
                    <span className="font-label-xs text-label-xs text-on-surface-variant font-sans">
                      POP
                    </span>
                    <span className="font-data-md text-data-md text-tertiary-fixed-dim font-bold">
                      {(scenario.winningStrategy.pop * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* Reasoning for change */}
                <div className="mt-4 pt-4 border-t border-outline-variant/30 flex flex-col gap-2">
                  <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-widest font-sans">
                    Reasoning for change (Quant Sensitivity)
                  </span>
                  <ul className="font-data-sm text-data-sm flex flex-col gap-1.5 text-on-surface">
                    {scenario.reasoning.map((r, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="material-symbols-outlined text-[14px] text-primary mt-0.5">
                          analytics
                        </span>
                        <span className="leading-snug">{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
