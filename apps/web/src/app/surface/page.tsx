'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { VolatilitySurface } from '@/types/voltron';
import { DEMO_VOL_SURFACE } from '@/fixtures/voltronFixtures';
import { VolSurface3DCanvas } from '@/components/surface/VolSurface3DCanvas';

const QUICK_SYMBOLS = ['SPY', 'QQQ', 'NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'META', 'GOOGL', 'AMD', 'PLTR', 'COIN'];

type SurfaceViewMode = '3D' | 'HEATMAP' | 'SMILE';

export default function VolatilitySurfacePage() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('SPY');
  const [customTickerInput, setCustomTickerInput] = useState<string>('');
  const [surfaceData, setSurfaceData] = useState<VolatilitySurface>(DEMO_VOL_SURFACE);
  const [viewMode, setViewMode] = useState<SurfaceViewMode>('3D');
  const [isScanning, setIsScanning] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadSurface = async (symbol: string) => {
    setIsScanning(true);
    setErrorMessage(null);
    try {
      const refreshed = await api.getVolSurface(symbol);
      setSurfaceData(refreshed);
      setSelectedSymbol(symbol);
    } catch (err: any) {
      console.warn('Failed to load surface:', err);
      const msg = err?.message || `Ticker '${symbol}' not found on US exchanges or Alpaca Paper Broker.`;
      setErrorMessage(msg);
    } finally {
      setIsScanning(false);
    }
  };

  useEffect(() => {
    loadSurface(selectedSymbol);
  }, [selectedSymbol]);

  const handleRunScan = async () => {
    await loadSurface(selectedSymbol);
  };

  return (
    <div className="flex flex-col w-full h-full gap-container-gap pb-container-gap">
      {/* Error Notification Banner */}
      {errorMessage && (
        <div className="bg-error/15 border-2 border-error/50 text-error px-4 py-3 rounded-sm flex items-center justify-between font-mono text-xs shadow-lg animate-fade-in">
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-error text-[20px]">error</span>
            <span className="font-bold">{errorMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            className="hover:text-on-surface transition-colors p-1"
          >
            <span className="material-symbols-outlined text-[16px]">close</span>
          </button>
        </div>
      )}

      {/* Top Workspace Grid (Surface + Sidebars) */}
      <div className="flex gap-container-gap h-[640px]">
        {/* Volatility Surface (Main Viewport) */}
        <div className="flex-1 bg-surface-container relative rounded-sm border border-outline-variant/30 flex flex-col overflow-hidden shadow-md">
          {/* Top Bar */}
          <div className="flex items-center justify-between p-panel-padding border-b border-outline-variant/30 bg-surface/80 backdrop-blur-sm z-10">
            <div className="flex items-center gap-3">
              <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">
                Implied Volatility Surface
              </h2>
              <div className="h-4 w-px bg-outline-variant" />
              
              {/* Custom Ticker Input Form */}
              <form
                onSubmit={async (e) => {
                  e.preventDefault();
                  if (customTickerInput.trim()) {
                    const sym = customTickerInput.trim().toUpperCase();
                    await loadSurface(sym);
                    setCustomTickerInput('');
                  }
                }}
                className="flex items-center gap-1.5 bg-surface border border-outline-variant/40 focus-within:border-primary/60 rounded-sm px-2 py-0.5 transition-all shadow-inner"
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
                {QUICK_SYMBOLS.slice(0, 11).map((sym) => (
                  <button
                    key={sym}
                    type="button"
                    onClick={() => setSelectedSymbol(sym)}
                    className={`px-1.5 py-0.5 text-[11px] font-mono font-bold rounded-sm transition-all ${
                      selectedSymbol === sym
                        ? 'bg-primary text-on-primary shadow-sm'
                        : 'text-on-surface-variant hover:text-primary hover:bg-surface-container-high'
                    }`}
                  >
                    {sym}
                  </button>
                ))}
              </div>

              <div className="flex gap-2 items-center">
                <span className="px-2 py-0.5 rounded-sm bg-primary/10 border border-primary/30 font-label-xs text-label-xs text-primary font-mono font-bold">
                  {surfaceData.underlying}
                </span>
                <span className="font-data-md text-data-md text-primary font-mono ml-1 font-bold">
                  ${surfaceData.spotPrice.toFixed(2)}
                </span>
              </div>
            </div>

            {/* View Switcher Controls */}
            <div className="flex items-center gap-3">
              <div className="flex bg-surface rounded-sm border border-outline-variant/50 p-1">
                {(['3D', 'HEATMAP', 'SMILE'] as SurfaceViewMode[]).map((mode) => (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => setViewMode(mode)}
                    className={`px-3 py-1 rounded-sm font-label-xs text-label-xs transition-colors ${
                      viewMode === mode
                        ? 'bg-surface-container-high text-primary font-bold shadow-sm'
                        : 'text-on-surface-variant hover:text-on-surface'
                    }`}
                  >
                    {mode}
                  </button>
                ))}
              </div>
              <button
                type="button"
                onClick={handleRunScan}
                disabled={isScanning}
                className="px-3 py-1.5 bg-primary/10 border border-primary/30 text-primary font-data-sm text-data-sm hover:bg-primary/20 transition-colors rounded-sm flex items-center gap-1 font-mono"
              >
                <span className={`material-symbols-outlined text-[14px] ${isScanning ? 'animate-spin' : ''}`}>sync</span>
                <span>Refresh</span>
              </button>
              <Link
                href="/tournament"
                className="px-3 py-1.5 bg-primary/10 border border-primary/30 text-primary font-data-sm text-data-sm hover:bg-primary/20 transition-colors rounded-sm flex items-center gap-1 font-mono"
              >
                <span>Tournament</span>
                <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
              </Link>
            </div>
          </div>

          {/* Surface Rendering Viewport */}
          <div className="flex-1 relative w-full bg-[#0a1012] overflow-hidden flex items-center justify-center">
            {/* Mode 1: 3D Surface View via HTML5 Canvas 3D Engine */}
            {viewMode === '3D' && <VolSurface3DCanvas surfaceData={surfaceData} />}

            {/* Mode 2: Heatmap View */}
            {viewMode === 'HEATMAP' && (
              <div className="w-full h-full p-8 flex flex-col justify-center max-w-2xl">
                <h4 className="font-label-xs text-label-xs text-outline uppercase tracking-widest mb-4">
                  {surfaceData.underlying} (${surfaceData.spotPrice.toFixed(2)}) Strike vs DTE Implied Volatility Heatmap
                </h4>
                {(() => {
                  const strikeStep = surfaceData.spotPrice >= 300 ? 5 : surfaceData.spotPrice >= 100 ? 2.5 : surfaceData.spotPrice >= 30 ? 1 : 0.5;
                  const centerStrike = Math.round(surfaceData.spotPrice / strikeStep) * strikeStep;
                  const heatmapStrikes = [
                    centerStrike - strikeStep * 2,
                    centerStrike - strikeStep,
                    centerStrike,
                    centerStrike + strikeStep,
                    centerStrike + strikeStep * 2,
                  ];
                  return (
                    <div className="grid grid-cols-6 gap-1 bg-surface-container-lowest p-2 border border-outline-variant/30">
                      <div className="p-2 text-label-xs font-label-xs text-outline font-mono">DTE \ K</div>
                      {heatmapStrikes.map((k) => (
                        <div key={k} className="p-2 text-center font-data-sm text-data-sm text-on-surface font-mono">
                          ${k.toFixed(1)}
                        </div>
                      ))}
                      {['7D', '14D', '30D', '45D'].map((dte, dIdx) => (
                        <React.Fragment key={dte}>
                          <div className="p-2 font-data-sm text-data-sm text-on-surface-variant font-mono">{dte}</div>
                          {heatmapStrikes.map((_, sIdx) => {
                            const atm = surfaceData.skewSnapshot?.atmIV || 18.2;
                            const putDelta = (surfaceData.skewSnapshot?.put25DeltaIV || (atm * 1.25)) - atm;
                            const callDelta = (surfaceData.skewSnapshot?.call25DeltaIV || (atm * 0.9)) - atm;
                            const skewOffset = sIdx === 0 ? putDelta : sIdx === 1 ? putDelta * 0.5 : sIdx === 2 ? 0.0 : sIdx === 3 ? callDelta * 0.5 : callDelta;
                            const ivVal = Math.max(5.0, atm + skewOffset + (4 - dIdx) * (atm * 0.04));

                            return (
                              <div
                                key={sIdx}
                                className={`p-2 text-center font-mono rounded-xs ${
                                  sIdx < 2
                                    ? 'bg-error/25 text-error font-bold'
                                    : sIdx === 2
                                    ? 'bg-primary/20 text-primary font-bold'
                                    : 'bg-primary/10 text-on-surface'
                                }`}
                              >
                                {ivVal.toFixed(1)}%
                              </div>
                            );
                          })}
                        </React.Fragment>
                      ))}
                    </div>
                  );
                })()}
              </div>
            )}

            {/* Mode 3: Dynamic Volatility Smile View */}
            {viewMode === 'SMILE' && (() => {
              const putIv = surfaceData.skewSnapshot?.put25DeltaIV || 21.4;
              const atmIv = surfaceData.skewSnapshot?.atmIV || 18.2;
              const callIv = surfaceData.skewSnapshot?.call25DeltaIV || 16.8;

              const maxIv = Math.max(putIv, atmIv, callIv, 40.0) * 1.15;
              const minIv = Math.min(putIv, atmIv, callIv, 12.0) * 0.75;
              const rangeIv = maxIv - minIv || 1;

              const getSmileY = (iv: number) => 180 - ((iv - minIv) / rangeIv) * 140;

              const putY = getSmileY(putIv);
              const atmY = getSmileY(atmIv);
              const callY = getSmileY(callIv);

              const startY = getSmileY(putIv * 1.10);
              const endY = getSmileY(callIv * 1.05);

              const smilePath = `M 50,${startY.toFixed(1)} Q 170,${putY.toFixed(1)} 300,${atmY.toFixed(1)} T 550,${endY.toFixed(1)}`;

              return (
                <div className="w-full h-full p-8 flex flex-col items-center justify-center max-w-3xl relative">
                  <h4 className="font-label-xs text-label-xs text-outline uppercase tracking-widest mb-4 self-start font-mono">
                    {surfaceData.underlying} (${surfaceData.spotPrice.toFixed(2)}) 30D Implied Volatility Smile &amp; Skew Curve
                  </h4>
                  <svg className="w-full h-64 border-b border-l border-outline-variant/30 p-4" viewBox="0 0 600 200">
                    {/* Grid */}
                    <line x1="0" y1="50" x2="600" y2="50" stroke="#192122" strokeDasharray="4 4" />
                    <line x1="0" y1="100" x2="600" y2="100" stroke="#192122" strokeDasharray="4 4" />
                    <line x1="0" y1="150" x2="600" y2="150" stroke="#192122" strokeDasharray="4 4" />
                    <line x1="300" y1="0" x2="300" y2="200" stroke="#3b494c" strokeWidth="1" />

                    {/* Smile Curve */}
                    <path
                      d={smilePath}
                      fill="none"
                      stroke="#00e5ff"
                      strokeWidth="3"
                    />

                    {/* Put Skew Highlight */}
                    <circle cx="170" cy={putY} r="5" fill="#ffb4ab" />
                    <text x="180" y={putY - 8} fill="#ffb4ab" fontSize="11" fontFamily="JetBrains Mono" fontWeight="bold">
                      25Δ Put ({putIv.toFixed(1)}%)
                    </text>

                    {/* ATM */}
                    <circle cx="300" cy={atmY} r="5" fill="#00daf3" />
                    <text x="310" y={atmY + 18} fill="#00daf3" fontSize="11" fontFamily="JetBrains Mono" fontWeight="bold">
                      ATM ({atmIv.toFixed(1)}%)
                    </text>

                    {/* Call Skew */}
                    <circle cx="430" cy={callY} r="5" fill="#cdbdff" />
                    <text x="440" y={callY - 8} fill="#cdbdff" fontSize="11" fontFamily="JetBrains Mono" fontWeight="bold">
                      25Δ Call ({callIv.toFixed(1)}%)
                    </text>
                  </svg>
                </div>
              );
            })()}
          </div>
        </div>

        {/* Right Sidebar (Term Structure & Skew) */}
        <div className="w-80 flex flex-col gap-container-gap shrink-0">
          {/* Term Structure Panel */}
          <div className="bg-surface-container rounded-sm border border-outline-variant/30 p-panel-padding flex flex-col shadow-sm flex-1 relative overflow-hidden group">
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-surface-variant group-hover:bg-primary-fixed-dim/50 transition-colors" />
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-label-xs text-label-xs text-outline uppercase tracking-widest">
                Term Structure
              </h3>
              <span className="material-symbols-outlined text-[16px] text-on-surface-variant">
                timeline
              </span>
            </div>

            <div className="flex-1 flex flex-col justify-between">
              {surfaceData.termStructure.map((term) => (
                <div
                  key={term.label}
                  className="flex items-center justify-between group/row p-2 -mx-2 hover:bg-surface-variant/50 rounded-sm transition-colors"
                >
                  <div className="flex flex-col">
                    <span className="font-data-sm text-data-sm text-on-surface font-mono">
                      {term.label}
                    </span>
                    <span className="font-label-xs text-label-xs text-on-surface-variant font-mono">
                      {term.dateLabel}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-16 h-1 bg-surface-variant rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary/80"
                        style={{ width: `${term.percentageOfMax}%` }}
                      />
                    </div>
                    <span className="font-data-lg text-data-lg text-primary text-right w-14 font-mono">
                      {term.iv.toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Put Skew Snapshot Panel */}
          <div className="bg-surface-container rounded-sm border border-outline-variant/30 p-panel-padding flex flex-col shadow-sm flex-1 relative overflow-hidden group">
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-surface-variant group-hover:bg-error/50 transition-colors" />
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-label-xs text-label-xs text-outline uppercase tracking-widest">
                30D Skew Snapshot
              </h3>
              <span className="material-symbols-outlined text-[16px] text-error">query_stats</span>
            </div>

            <div className="flex-1 flex flex-col gap-3">
              <div className="flex items-center justify-between bg-surface p-2 rounded-sm border border-outline-variant/20">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-error rounded-full" />
                  <span className="font-data-sm text-data-sm text-on-surface font-mono">25Δ Put</span>
                </div>
                <span className="font-data-md text-data-md text-error font-mono">
                  {surfaceData.skewSnapshot.put25DeltaIV.toFixed(1)}%
                </span>
              </div>

              <div className="flex items-center justify-between bg-surface p-2 rounded-sm border border-outline-variant/20">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-on-surface-variant rounded-full" />
                  <span className="font-data-sm text-data-sm text-on-surface font-mono">ATM</span>
                </div>
                <span className="font-data-md text-data-md text-on-surface font-mono">
                  {surfaceData.skewSnapshot.atmIV.toFixed(1)}%
                </span>
              </div>

              <div className="flex items-center justify-between bg-surface p-2 rounded-sm border border-outline-variant/20">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-primary/50 rounded-full" />
                  <span className="font-data-sm text-data-sm text-on-surface font-mono">25Δ Call</span>
                </div>
                <span className="font-data-md text-data-md text-on-surface-variant font-mono">
                  {surfaceData.skewSnapshot.call25DeltaIV.toFixed(1)}%
                </span>
              </div>

              <div className="mt-auto pt-2 border-t border-outline-variant/30 flex justify-between items-center">
                <span className="font-label-xs text-label-xs text-on-surface-variant uppercase">
                  P/C SKEW RATIO
                </span>
                <span className="font-data-md text-data-md text-error font-mono font-bold">
                  {surfaceData.skewSnapshot.skewRatio.toFixed(2)}x
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Anomalies Section */}
      <div className="bg-surface-container rounded-sm border border-outline-variant/30 p-panel-padding shadow-sm relative overflow-hidden group">
        <div className="absolute left-0 top-0 bottom-0 w-1 bg-surface-variant group-hover:bg-tertiary-fixed-dim/50 transition-colors" />
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px] text-tertiary-fixed-dim">
              warning
            </span>
            <h3 className="font-label-xs text-label-xs text-outline uppercase tracking-widest">
              Detected Market Anomalies (Quant MCP Feed)
            </h3>
          </div>
          <button
            type="button"
            onClick={handleRunScan}
            disabled={isScanning}
            className="font-label-xs text-label-xs text-primary hover:text-primary-fixed-dim uppercase tracking-wider flex items-center gap-1 disabled:opacity-50"
          >
            {isScanning ? 'Scanning...' : 'Run Scan'}{' '}
            <span className="material-symbols-outlined text-[14px]">play_arrow</span>
          </button>
        </div>

        <div className="grid grid-cols-3 gap-container-gap">
          {surfaceData.anomalies.map((anom) => {
            const isError = anom.category === 'SKEW';
            const isWarn = anom.category === 'TERM';
            const isLiq = anom.category === 'LIQUIDITY';

            return (
              <div
                key={anom.id}
                className={`bg-surface p-4 rounded-sm border border-outline-variant/20 flex flex-col gap-2 transition-colors cursor-pointer ${
                  isError
                    ? 'hover:border-error/50'
                    : isWarn
                    ? 'hover:border-tertiary-fixed-dim/50'
                    : 'hover:border-primary/50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <span
                    className={`font-data-md text-data-md font-semibold font-mono ${
                      isError ? 'text-error' : isWarn ? 'text-tertiary-fixed-dim' : 'text-on-surface'
                    }`}
                  >
                    {anom.name}
                  </span>
                  <span
                    className={`px-1.5 py-0.5 font-label-xs text-label-xs rounded-sm border font-mono ${
                      isError
                        ? 'bg-error/10 text-error border-error/20'
                        : isWarn
                        ? 'bg-tertiary-fixed-dim/10 text-tertiary-fixed-dim border-tertiary-fixed-dim/20'
                        : 'bg-primary/10 text-primary border-primary/20'
                    }`}
                  >
                    {anom.metricLabel}
                  </span>
                </div>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  {anom.description}
                </p>
                <div className="mt-2 flex items-center gap-2">
                  <div className="flex-1 h-0.5 bg-surface-variant">
                    <div
                      className={`h-full ${isError ? 'bg-error' : isWarn ? 'bg-tertiary-fixed-dim' : 'bg-primary'}`}
                      style={{ width: `${anom.percentile}%` }}
                    />
                  </div>
                  <span className="font-label-xs text-label-xs text-on-surface-variant font-mono">
                    {anom.confidence} CONF
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
