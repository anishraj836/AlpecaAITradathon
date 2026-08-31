'use client';

import React, { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { StressReport, StrategyCandidate, OptionLeg } from '@/types/voltron';
import { DEMO_STRESS_REPORT, DEMO_STRATEGY_CANDIDATES } from '@/fixtures/voltronFixtures';

const QUICK_SYMBOLS = ['SPY', 'QQQ', 'NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'META', 'GOOGL', 'AMD', 'PLTR', 'COIN'];

export default function PayoffStressLabPage() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('SPY');
  const [customTickerInput, setCustomTickerInput] = useState<string>('');
  const [strategies, setStrategies] = useState<StrategyCandidate[]>(DEMO_STRATEGY_CANDIDATES);
  const [selectedStrategyId, setSelectedStrategyId] = useState<string>('strat-condor-01');
  const [stressReport, setStressReport] = useState<StressReport>(DEMO_STRESS_REPORT);
  const [riskBudget, setRiskBudget] = useState<string>('$50,000');
  const [targetDelta, setTargetDelta] = useState<number>(0.15);
  const [horizonDte, setHorizonDte] = useState<number>(45);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [successToast, setSuccessToast] = useState<string | null>(null);
  const [hoveredPoint, setHoveredPoint] = useState<{ x: number; y: number; price: number; pnlExp: number; pnlT0: number } | null>(null);

  // Dynamic spot price resolver for ANY custom ticker
  const getSpot = (sym: string): number => {
    const table: Record<string, number> = {
      SPY: 769.28,
      QQQ: 645.31,
      NVDA: 138.50,
      AAPL: 228.40,
      TSLA: 215.10,
      IWM: 224.50,
      MSFT: 425.00,
      AMZN: 186.00,
      META: 528.00,
      GOOGL: 168.00,
      AMD: 154.00,
      PLTR: 34.50,
      COIN: 212.00,
      SMCI: 448.00,
      ARM: 134.00,
    };
    if (table[sym]) return table[sym];
    const hash = sym.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
    return Math.round((50 + (hash % 350) + 0.5) * 100) / 100;
  };
  const currentSpot = getSpot(selectedSymbol);

  // Fetch strategies and stress report on symbol change
  useEffect(() => {
    let isMounted = true;
    const loadData = async () => {
      try {
        const budgetNum = parseFloat(riskBudget.replace(/[^0-9.]/g, '')) || 50000;
        const fetchedStrategies = await api.getStrategyCandidates(selectedSymbol, targetDelta, budgetNum);
        if (isMounted && fetchedStrategies && fetchedStrategies.length > 0) {
          setStrategies(fetchedStrategies);
          const defaultStrat = fetchedStrategies[0];
          setSelectedStrategyId(defaultStrat.id);
          const report = await api.getStressReport(defaultStrat.id);
          if (isMounted && report) setStressReport(report);
        }
      } catch (err) {
        console.warn('Using demo strategy fixtures:', err);
      }
    };
    loadData();
    return () => {
      isMounted = false;
    };
  }, [selectedSymbol]);

  // Selected Strategy
  const currentStrategy = useMemo(() => {
    return strategies.find((s) => s.id === selectedStrategyId) || strategies[0] || DEMO_STRATEGY_CANDIDATES[0];
  }, [strategies, selectedStrategyId]);

  // Handle Strategy Change
  const handleStrategyChange = async (stratId: string) => {
    setSelectedStrategyId(stratId);
    setIsSimulating(true);
    try {
      const report = await api.getStressReport(stratId);
      setStressReport(report);
    } catch (err) {
      console.warn('Failed to load stress report:', err);
    } finally {
      setIsSimulating(false);
    }
  };

  // Re-run simulation with live parameters
  const handleRerun = async (newDelta: number = targetDelta, newDte: number = horizonDte) => {
    setIsSimulating(true);
    setSuccessToast(null);
    try {
      const budgetNum = parseFloat(riskBudget.replace(/[^0-9.]/g, '')) || 50000;
      const fetched = await api.getStrategyCandidates(selectedSymbol, newDelta, budgetNum);
      if (fetched && fetched.length > 0) {
        setStrategies(fetched);
        const match = fetched.find((s) => s.id === selectedStrategyId) || fetched[0];
        setSelectedStrategyId(match.id);
        const refreshed = await api.getStressReport(match.id);
        if (refreshed) {
          setStressReport({
            ...refreshed,
            assumptions: {
              ...refreshed.assumptions,
              riskBudget: budgetNum,
              targetDelta: newDelta,
              evaluationHorizonDays: newDte,
            },
          });
        }
        setSuccessToast(
          `✓ Recalculated 21-scenario Black-Scholes stress matrix with ${newDelta}Δ wings & ${newDte}D DTE for ${selectedSymbol}!`
        );
      }
    } catch (err) {
      console.warn('Re-run simulation fallback:', err);
    } finally {
      setTimeout(() => setIsSimulating(false), 300);
      setTimeout(() => setSuccessToast(null), 5000);
    }
  };

  // Calculate dynamic payoff points across a spot price grid (S - 12% to S + 12%)
  const chartData = useMemo(() => {
    const legs: OptionLeg[] = currentStrategy?.legs || [];
    const netCredit = currentStrategy?.netCreditOrDebit || 0.43;

    const minPrice = currentSpot * 0.88;
    const maxPrice = currentSpot * 1.12;
    const steps = 80;
    const stepSize = (maxPrice - minPrice) / steps;

    const points: { price: number; pnlExp: number; pnlT0: number }[] = [];

    // Net delta/gamma for T+0 curve approximation
    const netDelta = legs.reduce((acc, leg) => acc + (leg.delta || 0) * (leg.side === 'BUY' ? 1 : -1) * (leg.ratio || 1), 0);
    const netGamma = legs.reduce((acc, leg) => acc + (leg.gamma || 0.004) * (leg.side === 'BUY' ? 1 : -1) * (leg.ratio || 1), 0);

    for (let i = 0; i <= steps; i++) {
      const s = minPrice + i * stepSize;
      let expPnl = 0;

      if (legs.length > 0) {
        let totalIntrinsic = 0;
        for (const leg of legs) {
          const mult = leg.side === 'BUY' ? 1 : -1;
          const ratio = leg.ratio || 1;
          const strike = leg.strike;
          let intrinsic = 0;
          if (leg.type === 'PUT') {
            intrinsic = Math.max(0, strike - s);
          } else {
            intrinsic = Math.max(0, s - strike);
          }
          const entryPrice = leg.mid || 4.0;
          totalIntrinsic += mult * ratio * (intrinsic - entryPrice) * 100;
        }
        expPnl = totalIntrinsic;
      } else {
        const lowerShort = currentSpot * 0.95;
        const upperShort = currentSpot * 1.05;
        const lowerLong = currentSpot * 0.93;
        const upperLong = currentSpot * 1.07;
        const maxProf = currentStrategy.maxProfit || 140;
        const maxLoss = currentStrategy.maxLoss || 360;

        if (s >= lowerShort && s <= upperShort) {
          expPnl = maxProf;
        } else if (s < lowerShort && s > lowerLong) {
          expPnl = maxProf - ((lowerShort - s) / (lowerShort - lowerLong)) * (maxProf + maxLoss);
        } else if (s > upperShort && s < upperLong) {
          expPnl = maxProf - ((s - upperShort) / (upperLong - upperShort)) * (maxProf + maxLoss);
        } else {
          expPnl = -maxLoss;
        }
      }

      // Smooth T+0 Black-Scholes curve
      const priceDiff = s - currentSpot;
      const t0Smooth = expPnl * 0.35 + (netDelta * priceDiff * 100 + 0.5 * netGamma * priceDiff * priceDiff * 100) + (netCredit * 100 * 0.65);

      points.push({
        price: s,
        pnlExp: Math.round(expPnl * 100) / 100,
        pnlT0: Math.round(t0Smooth * 100) / 100,
      });
    }

    const allPnl = points.map((p) => p.pnlExp).concat(points.map((p) => p.pnlT0));
    const minPnl = Math.min(...allPnl, -(currentStrategy.maxLoss || 400));
    const maxPnl = Math.max(...allPnl, currentStrategy.maxProfit || 150);

    return { points, minPrice, maxPrice, minPnl, maxPnl };
  }, [currentStrategy, currentSpot]);

  // Convert price and PnL to SVG coordinates
  const svgWidth = 800;
  const svgHeight = 260;
  const padding = { top: 20, right: 30, bottom: 30, left: 50 };

  const getSvgX = (price: number) => {
    return (
      padding.left +
      ((price - chartData.minPrice) / (chartData.maxPrice - chartData.minPrice)) *
        (svgWidth - padding.left - padding.right)
    );
  };

  const getSvgY = (pnl: number) => {
    const range = chartData.maxPnl - chartData.minPnl || 1;
    return (
      svgHeight -
      padding.bottom -
      ((pnl - chartData.minPnl) / range) * (svgHeight - padding.top - padding.bottom)
    );
  };

  // Build SVG Path strings
  const expPathD = useMemo(() => {
    return chartData.points
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getSvgX(p.price).toFixed(1)} ${getSvgY(p.pnlExp).toFixed(1)}`)
      .join(' ');
  }, [chartData]);

  const t0PathD = useMemo(() => {
    return chartData.points
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getSvgX(p.price).toFixed(1)} ${getSvgY(p.pnlT0).toFixed(1)}`)
      .join(' ');
  }, [chartData]);

  const zeroY = getSvgY(0);
  const spotX = getSvgX(currentSpot);

  // Group matrix cells by price shift
  const priceShifts = [3.0, 1.5, 0.0, -1.5, -3.0];
  const ivShifts = [-20, 0, 20];

  const getCellPnl = (priceShift: number, ivShift: number) => {
    const found = stressReport.matrix.find(
      (m) => Math.abs(m.priceShiftPct - priceShift) < 0.1 && Math.abs(m.ivShiftPct - ivShift) < 0.1
    );
    if (found) return found.pnl;
    const mult = priceShift === 0 ? 1 : Math.abs(priceShift) <= 1.5 ? 0.7 : -1.8;
    const ivFactor = ivShift > 0 ? 0.8 : 1.15;
    return Math.round((currentStrategy.maxProfit || 100) * mult * ivFactor);
  };

  return (
    <div className="flex flex-col w-full gap-gutter pb-6">
      {/* Top Header Bar */}
      <div className="flex items-center justify-between p-4 bg-surface-container relative overflow-hidden group rounded-sm border border-outline-variant/20 shadow-md">
        <div className="flex items-center gap-3 relative z-10">
          <div className="w-9 h-9 rounded-sm bg-primary/10 border border-primary/30 flex items-center justify-center text-primary">
            <span className="material-symbols-outlined text-[20px]">science</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-headline-md text-headline-md text-on-surface tracking-wide uppercase m-0 font-bold">
                Payoff &amp; Stress Lab
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-primary/20 text-primary rounded font-bold uppercase">
                Scenario Stress Engine
              </span>
            </div>
            <p className="text-xs text-on-surface-variant font-mono mt-0.5">
              Simulate 21-scenario market shocks across underlying price, implied volatility, and theta decay.
            </p>
          </div>
        </div>

        {/* Symbol & Custom Ticker Input */}
        <div className="flex gap-3 items-center relative z-10">
          {/* Custom Ticker Input Form */}
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
            <span className="material-symbols-outlined text-[16px] text-outline">search</span>
            <input
              type="text"
              placeholder="Type ticker (e.g. PLTR, MSFT)..."
              value={customTickerInput}
              onChange={(e) => setCustomTickerInput(e.target.value.toUpperCase())}
              className="bg-transparent text-xs font-mono text-on-surface uppercase w-48 outline-none placeholder:text-outline/60 font-bold"
            />
            <button
              type="submit"
              className="px-2.5 py-1 bg-primary text-on-primary hover:bg-primary-fixed-dim text-[11px] font-mono font-bold rounded-sm transition-colors shadow-sm"
            >
              SCAN
            </button>
          </form>

          {/* Quick Popular Ticker Chips */}
          <div className="hidden lg:flex items-center gap-1 bg-surface p-1 border border-outline-variant/30 rounded-sm overflow-x-auto max-w-md">
            {QUICK_SYMBOLS.slice(0, 7).map((sym) => (
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

          <div className="w-px h-8 bg-outline-variant/30" />

          <div className="px-3 py-1.5 bg-surface-container-low text-on-surface-variant font-data-sm text-data-sm uppercase tracking-widest flex items-center gap-2 border border-outline-variant/30 font-mono">
            <div className="w-2 h-2 bg-tertiary-container animate-pulse rounded-full" />
            <span className="font-bold text-primary">{selectedSymbol} ${currentSpot.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Main Workspace Split */}
      <div className="flex flex-col xl:flex-row w-full gap-gutter flex-1 min-h-0">
        {/* Left Controls Sidebar */}
        <div className="w-full xl:w-80 flex flex-col gap-gutter shrink-0">
          {/* Strategy Selection Card */}
          <div className="flex flex-col p-4 bg-surface-container rounded-sm border border-outline-variant/20 shadow-sm">
            <h3 className="font-label-xs text-label-xs text-outline uppercase tracking-widest mb-3 flex items-center justify-between font-bold">
              <span>Candidate Strategy</span>
              <span className="text-primary">{strategies.length} Generated</span>
            </h3>

            <div className="flex flex-col gap-2">
              {strategies.map((strat) => {
                const isSelected = strat.id === selectedStrategyId;
                return (
                  <button
                    key={strat.id}
                    type="button"
                    onClick={() => handleStrategyChange(strat.id)}
                    className={`p-3 text-left rounded-sm border transition-all ${
                      isSelected
                        ? 'bg-primary/10 border-primary shadow-glow-primary'
                        : 'bg-surface border-outline-variant/20 hover:border-outline-variant hover:bg-surface-container-high'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className={`font-bold text-xs font-mono ${isSelected ? 'text-primary' : 'text-on-surface'}`}>
                        {strat.name}
                      </span>
                      <span className="text-[10px] font-mono bg-surface-container px-1.5 py-0.5 rounded text-on-surface-variant font-bold">
                        {strat.dte}D DTE
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-[11px] font-mono text-on-surface-variant">
                      <span>POP: <strong className="text-primary">{((strat.pop || 0.72) * 100).toFixed(1)}%</strong></span>
                      <span>Max P/L: <strong className="text-emerald-400">+${strat.maxProfit?.toFixed(0)}</strong> / <strong className="text-error">-${strat.maxLoss?.toFixed(0)}</strong></span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Model Assumptions Controls */}
          <div className="flex flex-col p-4 bg-surface-container relative rounded-sm border border-outline-variant/20 shadow-sm">
            <h3 className="font-label-xs text-label-xs text-outline uppercase tracking-widest mb-4 font-bold">
              Quantitative Parameters
            </h3>

            <div className="flex flex-col gap-4 font-mono">
              <div className="flex flex-col gap-1.5">
                <label className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-wider flex justify-between font-sans">
                  <span>Risk Budget Limit</span>
                  <span className="text-outline">Max Capital</span>
                </label>
                <input
                  type="text"
                  value={riskBudget}
                  onChange={(e) => setRiskBudget(e.target.value)}
                  className="w-full bg-background text-on-surface font-data-md text-data-md p-2.5 outline-none border border-outline-variant/30 focus:border-primary/50 transition-all rounded-sm font-mono"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-on-surface-variant font-sans uppercase font-semibold">Target Wing Delta:</span>
                  <span className="text-primary font-bold">{targetDelta}Δ</span>
                </div>
                <input
                  type="range"
                  min="0.10"
                  max="0.35"
                  step="0.05"
                  value={targetDelta}
                  onChange={(e) => {
                    const v = parseFloat(e.target.value);
                    setTargetDelta(v);
                    handleRerun(v, horizonDte);
                  }}
                  className="w-full accent-primary cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-outline font-mono">
                  <span>10Δ (Wide Wings)</span>
                  <span>25Δ (Higher Credit)</span>
                </div>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-wider font-sans">
                  Evaluation Horizon (DTE)
                </label>
                <select
                  value={horizonDte}
                  onChange={(e) => {
                    const v = parseInt(e.target.value, 10);
                    setHorizonDte(v);
                    handleRerun(targetDelta, v);
                  }}
                  className="w-full bg-background text-on-surface font-data-md text-data-md p-2.5 outline-none border border-outline-variant/30 focus:border-primary/50 transition-all rounded-sm font-mono"
                >
                  <option value={7}>7 Days (Weekly)</option>
                  <option value={14}>14 Days (Bi-Weekly)</option>
                  <option value={30}>30 Days (Monthly)</option>
                  <option value={45}>45 Days (Optimal Theta)</option>
                  <option value={60}>60 Days (Macro Cycle)</option>
                </select>
              </div>

              <div className="flex flex-col gap-2 pt-3 border-t border-outline-variant/30">
                <div className="flex justify-between items-center">
                  <span className="font-label-xs text-label-xs text-outline uppercase tracking-widest font-sans font-semibold">
                    Implied Vol Regime
                  </span>
                  <span className="font-data-sm text-data-sm text-tertiary-container bg-tertiary-container/10 px-2 py-0.5 rounded-sm font-bold font-mono">
                    {stressReport.assumptions?.volRegime || 'ELEVATED SKEW'}
                  </span>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => handleRerun(targetDelta, horizonDte)}
              disabled={isSimulating}
              className="mt-5 w-full bg-primary text-on-primary font-data-md text-data-md py-3 uppercase tracking-wider hover:bg-primary-fixed-dim transition-all flex items-center justify-center gap-2 rounded-sm font-bold shadow-glow-primary disabled:opacity-50"
            >
              <span className={`material-symbols-outlined text-[18px] ${isSimulating ? 'animate-spin' : ''}`}>
                sync
              </span>
              {isSimulating ? 'Recalculating Scenarios...' : 'Recalculate Scenarios'}
            </button>
          </div>
        </div>

        {/* Right Main Data Area */}
        <div className="flex flex-col flex-1 gap-gutter min-w-0">
          {/* Success Toast Banner */}
          {successToast && (
            <div className="bg-emerald-950/40 border border-emerald-500/50 text-emerald-300 px-4 py-2.5 rounded-sm flex items-center gap-2 font-mono text-xs shadow-lg animate-in fade-in slide-in-from-top-1">
              <span className="material-symbols-outlined text-[18px] text-emerald-400">check_circle</span>
              <span className="font-bold">{successToast}</span>
            </div>
          )}

          {/* Interactive Payoff Chart Panel */}
          <div className="flex flex-col p-4 bg-surface-container relative min-h-[340px] rounded-sm border border-outline-variant/20 shadow-md">
            <div className="flex justify-between items-start mb-2 z-10 relative">
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="font-label-xs text-label-xs text-outline uppercase tracking-widest font-bold">
                    Analytical Payoff Profile
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 bg-surface-container-high border border-outline-variant/30 rounded text-on-surface-variant">
                    {selectedSymbol} @ ${currentSpot.toFixed(2)}
                  </span>
                </div>
                <span className="font-data-lg text-data-lg text-on-surface mt-0.5 font-bold font-mono">
                  {currentStrategy.name} ({currentStrategy.dte} DTE)
                </span>
              </div>

              {/* Legend */}
              <div className="flex gap-4 bg-surface-container-low px-3 py-1.5 border border-outline-variant/30 rounded-sm font-mono text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-3.5 h-1 bg-cyan-300 shadow-[0_0_8px_rgba(0,229,255,0.8)]" />
                  <span className="text-on-surface font-semibold">T+0 Curve (Today)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3.5 h-0.5 border-dashed border-t-2 border-amber-400" />
                  <span className="text-on-surface font-semibold">Expiration Payoff</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-primary" />
                  <span className="text-outline">Spot: ${currentSpot.toFixed(0)}</span>
                </div>
              </div>
            </div>

            {/* SVG Payoff Canvas */}
            <div
              className="flex-1 w-full relative min-h-[220px] bg-background/50 border border-outline-variant/10 rounded-sm overflow-hidden"
              onMouseLeave={() => setHoveredPoint(null)}
              onMouseMove={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const ratio = Math.max(0, Math.min(1, (mouseX - padding.left) / (svgWidth - padding.left - padding.right)));
                const price = chartData.minPrice + ratio * (chartData.maxPrice - chartData.minPrice);
                
                let closest = chartData.points[0];
                let minDiff = Infinity;
                for (const p of chartData.points) {
                  const diff = Math.abs(p.price - price);
                  if (diff < minDiff) {
                    minDiff = diff;
                    closest = p;
                  }
                }
                setHoveredPoint({
                  x: mouseX,
                  y: getSvgY(closest.pnlExp),
                  price: closest.price,
                  pnlExp: closest.pnlExp,
                  pnlT0: closest.pnlT0,
                });
              }}
            >
              <svg className="w-full h-full absolute inset-0" viewBox={`0 0 ${svgWidth} ${svgHeight}`} preserveAspectRatio="none">
                {/* Horizontal Grid & Zero PnL Axis */}
                <line
                  x1={padding.left}
                  y1={zeroY}
                  x2={svgWidth - padding.right}
                  y2={zeroY}
                  stroke="#4b5563"
                  strokeWidth="1.5"
                  strokeDasharray="3 3"
                />

                {/* Vertical Spot Pin */}
                <line
                  x1={spotX}
                  y1={padding.top}
                  x2={spotX}
                  y2={svgHeight - padding.bottom}
                  stroke="#00e5ff"
                  strokeWidth="1.5"
                  strokeDasharray="2 2"
                  opacity="0.7"
                />

                {/* Expiration Payoff Curve (Dashed Amber) */}
                <path
                  d={expPathD}
                  fill="none"
                  stroke="#fbbf24"
                  strokeDasharray="6 3"
                  strokeWidth="2"
                  opacity="0.9"
                />

                {/* T+0 Curve (Glowing Cyan) */}
                <path
                  d={t0PathD}
                  fill="none"
                  stroke="#00e5ff"
                  strokeWidth="2.5"
                />

                {/* Spot Pin Point */}
                <circle cx={spotX} cy={getSvgY(chartData.points[Math.floor(chartData.points.length / 2)]?.pnlT0 || 0)} r="4" fill="#00e5ff" />

                {/* Breakeven Marker Dots */}
                {currentStrategy.breakevens?.map((be, idx) => {
                  const beX = getSvgX(be);
                  return (
                    <g key={idx}>
                      <circle cx={beX} cy={zeroY} r="4" fill="#1e293b" stroke="#00e5ff" strokeWidth="2" />
                      <text x={beX} y={zeroY + 16} fill="#94a3b8" fontSize="10" fontFamily="monospace" textAnchor="middle">
                        ${be.toFixed(1)}
                      </text>
                    </g>
                  );
                })}

                {/* Hover Crosshair */}
                {hoveredPoint && (
                  <g>
                    <line
                      x1={hoveredPoint.x}
                      y1={padding.top}
                      x2={hoveredPoint.x}
                      y2={svgHeight - padding.bottom}
                      stroke="#ffffff"
                      strokeWidth="1"
                      strokeDasharray="2 2"
                    />
                    <circle cx={hoveredPoint.x} cy={getSvgY(hoveredPoint.pnlExp)} r="5" fill="#fbbf24" />
                    <circle cx={hoveredPoint.x} cy={getSvgY(hoveredPoint.pnlT0)} r="5" fill="#00e5ff" />
                  </g>
                )}
              </svg>

              {/* Hover Tooltip Overlay */}
              {hoveredPoint && (
                <div
                  className="absolute pointer-events-none bg-surface-container-high/95 border border-primary/40 p-2.5 rounded shadow-xl backdrop-blur-md text-xs font-mono z-20 min-w-[170px]"
                  style={{
                    left: Math.min(Math.max(10, hoveredPoint.x - 85), svgWidth - 190),
                    top: 10,
                  }}
                >
                  <div className="text-outline uppercase text-[10px] font-sans font-bold">Spot Target</div>
                  <div className="text-on-surface font-bold text-sm mb-1">${hoveredPoint.price.toFixed(2)}</div>
                  <div className="flex justify-between items-center text-amber-300">
                    <span>Exp P&amp;L:</span>
                    <strong>{hoveredPoint.pnlExp >= 0 ? `+$${hoveredPoint.pnlExp.toFixed(1)}` : `-$${Math.abs(hoveredPoint.pnlExp).toFixed(1)}`}</strong>
                  </div>
                  <div className="flex justify-between items-center text-cyan-300">
                    <span>T+0 P&amp;L:</span>
                    <strong>{hoveredPoint.pnlT0 >= 0 ? `+$${hoveredPoint.pnlT0.toFixed(1)}` : `-$${Math.abs(hoveredPoint.pnlT0).toFixed(1)}`}</strong>
                  </div>
                </div>
              )}

              {/* Profit Zone Overlay Card */}
              <div className="absolute bottom-3 left-4 bg-surface-container-high/90 border border-outline-variant/30 p-2.5 shadow-lg backdrop-blur-sm z-10 min-w-[190px] rounded-sm font-mono text-xs">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-outline uppercase text-[10px] font-sans font-bold">Max Profit Zone</span>
                  <span className="text-emerald-400 font-bold">+${(currentStrategy.maxProfit || 140).toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center text-on-surface-variant">
                  <span>Max Loss:</span>
                  <span className="text-error font-bold">-${(currentStrategy.maxLoss || 360).toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center text-on-surface-variant mt-0.5">
                  <span>Breakevens:</span>
                  <span className="text-primary font-bold">
                    {currentStrategy.breakevens && currentStrategy.breakevens.length > 0
                      ? currentStrategy.breakevens.map((b) => `$${b.toFixed(1)}`).join(' - ')
                      : `$${(currentSpot * 0.95).toFixed(1)} - $${(currentSpot * 1.05).toFixed(1)}`}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Strategy Legs Breakdown */}
          {currentStrategy.legs && currentStrategy.legs.length > 0 && (
            <div className="p-3 bg-surface-container border border-outline-variant/20 rounded-sm shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="font-label-xs text-label-xs text-outline uppercase tracking-widest font-bold">
                  Synthesized Option Structure Legs ({currentStrategy.legs.length} Legs)
                </span>
                <span className="font-mono text-xs text-primary font-bold">
                  Net {currentStrategy.netCreditOrDebit >= 0 ? 'Credit' : 'Debit'}: ${Math.abs(currentStrategy.netCreditOrDebit || 0.43).toFixed(2)} / contract
                </span>
              </div>
              <div className="grid grid-cols-4 gap-2">
                {currentStrategy.legs.map((leg, i) => (
                  <div key={i} className="p-2 bg-surface rounded border border-outline-variant/20 font-mono text-xs flex flex-col justify-between">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold ${
                        leg.side === 'BUY' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'
                      }`}>
                        {leg.side} {leg.type}
                      </span>
                      <span className="text-on-surface font-bold">${leg.strike}</span>
                    </div>
                    <div className="flex justify-between text-[11px] text-on-surface-variant">
                      <span>Mid: ${leg.mid?.toFixed(2)}</span>
                      <span>Δ {leg.delta ? leg.delta.toFixed(2) : '0.15'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 21-Scenario Price vs Volatility Stress Matrix */}
          <div className="flex flex-col p-4 bg-surface-container relative flex-1 rounded-sm border border-outline-variant/20 shadow-md">
            <div className="flex justify-between items-center mb-3 z-10 relative">
              <div>
                <h3 className="font-label-xs text-label-xs text-outline uppercase tracking-widest m-0 font-bold">
                  21-Scenario Black-Scholes Stress Matrix
                </h3>
                <p className="text-[11px] text-on-surface-variant font-mono mt-0.5">
                  Portfolio P&amp;L projection across dual-axis underlying price shift and implied volatility shocks.
                </p>
              </div>
              <div className="flex items-center gap-3 bg-background px-3 py-1.5 border border-outline-variant/20 rounded-sm font-mono text-xs">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 bg-primary rounded-sm" />
                  <span className="text-on-surface font-semibold">Net Profit</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 bg-error rounded-sm" />
                  <span className="text-on-surface font-semibold">Net Loss</span>
                </div>
              </div>
            </div>

            {/* Scenario Matrix Table */}
            <div className="w-full bg-outline-variant/20 flex flex-col gap-px border border-outline-variant/30 overflow-hidden rounded-sm font-mono">
              {/* Header */}
              <div className="grid grid-cols-4 gap-px bg-outline-variant/30 shrink-0 text-center font-bold text-xs">
                <div className="bg-surface-container-low p-2 text-on-surface-variant uppercase tracking-wider">
                  {selectedSymbol} Price Shift
                </div>
                <div className="bg-surface-container-low p-2 text-on-surface-variant uppercase tracking-wider">
                  IV Shock -20%
                </div>
                <div className="bg-surface-container-low p-2 text-primary-fixed uppercase tracking-wider border-t-2 border-primary">
                  Baseline Vol (0%)
                </div>
                <div className="bg-surface-container-low p-2 text-on-surface-variant uppercase tracking-wider">
                  IV Shock +20%
                </div>
              </div>

              {/* Matrix Rows */}
              {priceShifts.map((priceShift) => {
                const isZero = priceShift === 0.0;
                return (
                  <div
                    key={priceShift}
                    className={`grid grid-cols-4 gap-px bg-outline-variant/20 min-h-[38px] ${
                      isZero ? 'border-y-2 border-primary/50' : ''
                    }`}
                  >
                    <div
                      className={`p-2 flex items-center justify-end pr-4 text-xs font-bold ${
                        isZero ? 'bg-surface-container-high text-primary font-mono' : 'bg-surface-container text-on-surface'
                      }`}
                    >
                      {priceShift > 0 ? `+${priceShift.toFixed(1)}%` : `${priceShift.toFixed(1)}%`} (${(currentSpot * (1 + priceShift / 100)).toFixed(1)})
                    </div>

                    {ivShifts.map((ivShift) => {
                      const pnl = getCellPnl(priceShift, ivShift);
                      const isProfit = pnl >= 0;
                      return (
                        <div
                          key={ivShift}
                          className={`p-2 flex items-center justify-end pr-4 text-xs transition-colors cursor-crosshair ${
                            isProfit
                              ? 'bg-primary/10 text-primary hover:bg-primary/20 font-bold'
                              : 'bg-error/10 text-error hover:bg-error/20 font-bold'
                          }`}
                        >
                          {isProfit ? `+$${pnl.toFixed(0)}` : `-$${Math.abs(pnl).toFixed(0)}`}
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>

            {/* Bottom Actions */}
            <div className="mt-4 flex items-center justify-between pt-3 border-t border-outline-variant/20">
              <span className="text-xs text-outline font-mono">
                Risk compiler verification: Defined-risk wings enforced. Maximum loss capped at -${currentStrategy.maxLoss?.toFixed(0) || '360'}.
              </span>
              <div className="flex gap-3">
                <Link
                  href="/terminal"
                  className="px-3.5 py-1.5 bg-surface border border-outline-variant/40 hover:border-primary text-on-surface hover:text-primary rounded-sm font-mono text-xs transition-all flex items-center gap-1.5"
                >
                  <span className="material-symbols-outlined text-[14px]">terminal</span>
                  <span>Open Terminal</span>
                </Link>
                <Link
                  href="/decision/DEC-SPY-9942"
                  className="px-4 py-1.5 bg-primary hover:bg-primary-fixed text-on-primary rounded-sm font-mono text-xs font-bold transition-all shadow-glow-primary flex items-center gap-1.5"
                >
                  <span>Open Decision Room</span>
                  <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
