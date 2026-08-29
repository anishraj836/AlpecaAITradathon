'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { VolatilitySurface } from '@/types/voltron';
import { DEMO_VOL_SURFACE } from '@/fixtures/voltronFixtures';

type SurfaceViewMode = '3D' | 'HEATMAP' | 'SMILE';

export default function VolatilitySurfacePage() {
  const [surfaceData, setSurfaceData] = useState<VolatilitySurface>(DEMO_VOL_SURFACE);
  const [viewMode, setViewMode] = useState<SurfaceViewMode>('3D');
  const [isScanning, setIsScanning] = useState(false);

  useEffect(() => {
    let isMounted = true;
    api.getVolSurface('SPY').then((data) => {
      if (isMounted) setSurfaceData(data);
    });
    return () => {
      isMounted = false;
    };
  }, []);

  const handleRunScan = async () => {
    setIsScanning(true);
    try {
      const refreshed = await api.getVolSurface('SPY');
      setSurfaceData(refreshed);
    } finally {
      setTimeout(() => setIsScanning(false), 600);
    }
  };

  return (
    <div className="flex flex-col w-full h-full gap-container-gap pb-container-gap">
      {/* Top Workspace Grid (Surface + Sidebars) */}
      <div className="flex gap-container-gap h-[640px]">
        {/* Volatility Surface (Main Viewport) */}
        <div className="flex-1 bg-surface-container relative rounded-sm border border-outline-variant/30 flex flex-col overflow-hidden shadow-md">
          {/* Top Bar */}
          <div className="flex items-center justify-between p-panel-padding border-b border-outline-variant/30 bg-surface/80 backdrop-blur-sm z-10">
            <div className="flex items-center gap-4">
              <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">
                Implied Volatility Surface
              </h2>
              <div className="h-4 w-px bg-outline-variant" />
              <div className="flex gap-2 items-center">
                <span className="px-2 py-0.5 rounded-sm bg-primary/10 border border-primary/30 font-label-xs text-label-xs text-primary font-mono">
                  {surfaceData.underlying}
                </span>
                <span className="px-2 py-0.5 rounded-sm bg-surface-variant text-on-surface-variant font-label-xs text-label-xs">
                  EQUITY
                </span>
                <span className="font-data-md text-data-md text-primary-fixed-dim font-mono ml-2">
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
              <Link
                href="/tournament"
                className="px-3 py-1.5 bg-primary/10 border border-primary/30 text-primary font-data-sm text-data-sm hover:bg-primary/20 transition-colors rounded-sm flex items-center gap-1"
              >
                <span>Tournament</span>
                <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
              </Link>
            </div>
          </div>

          {/* Surface Rendering Viewport */}
          <div className="flex-1 relative w-full bg-[#0a1012] overflow-hidden flex items-center justify-center">
            {/* Abstract radial glow */}
            <div className="absolute inset-0 opacity-40 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/20 via-surface to-background pointer-events-none" />

            {/* Mode 1: 3D Surface View */}
            {viewMode === '3D' && (
              <div className="relative w-full h-full flex items-center justify-center p-8">
                {/* 3D Grid lines */}
                <svg className="absolute inset-0 w-full h-full opacity-20 pointer-events-none">
                  <defs>
                    <pattern id="vol-grid-pattern" width="40" height="40" patternUnits="userSpaceOnUse">
                      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#849396" strokeWidth="1" />
                    </pattern>
                  </defs>
                  <rect
                    width="100%"
                    height="100%"
                    fill="url(#vol-grid-pattern)"
                    style={{ transform: 'perspective(500px) rotateX(60deg) scale(2)', transformOrigin: 'top center' }}
                  />
                </svg>

                {/* Parametric Wireframe Mesh Mockup */}
                <svg className="w-[85%] h-[80%] opacity-90 drop-shadow-[0_0_20px_rgba(0,229,255,0.2)]" viewBox="0 0 800 400">
                  {/* Surface Contour Rings */}
                  <path
                    d="M 50,300 Q 200,180 400,220 T 750,260"
                    fill="none"
                    stroke="#00e5ff"
                    strokeWidth="2.5"
                  />
                  <path
                    d="M 80,260 Q 220,140 420,180 T 720,220"
                    fill="none"
                    stroke="#00daf3"
                    strokeWidth="2"
                    strokeDasharray="4 2"
                  />
                  <path
                    d="M 120,220 Q 240,100 440,140 T 680,180"
                    fill="none"
                    stroke="#cdbdff"
                    strokeWidth="2"
                  />
                  <path
                    d="M 160,180 Q 260,70 460,100 T 640,140"
                    fill="none"
                    stroke="#fec931"
                    strokeWidth="1.5"
                  />
                  <path
                    d="M 200,140 Q 280,40 480,70 T 600,100"
                    fill="none"
                    stroke="#ffb4ab"
                    strokeWidth="1.5"
                  />

                  {/* Connecting Ribs */}
                  <path d="M 50,300 L 200,140" stroke="#3b494c" strokeWidth="1" strokeDasharray="2 2" />
                  <path d="M 200,180 L 280,40" stroke="#3b494c" strokeWidth="1" strokeDasharray="2 2" />
                  <path d="M 400,220 L 480,70" stroke="#00e5ff" strokeWidth="1.5" />
                  <path d="M 600,240 L 540,85" stroke="#3b494c" strokeWidth="1" strokeDasharray="2 2" />
                  <path d="M 750,260 L 600,100" stroke="#3b494c" strokeWidth="1" strokeDasharray="2 2" />

                  {/* ATM Focal Node */}
                  <circle cx="400" cy="220" r="5" fill="#00e5ff" className="animate-ping" />
                  <circle cx="400" cy="220" r="4" fill="#00363d" stroke="#00e5ff" strokeWidth="2" />
                </svg>

                {/* Simulated Hover Tooltip */}
                <div className="absolute top-1/3 left-1/3 bg-surface-container-highest border border-outline-variant p-3 rounded-sm shadow-xl z-20 flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                    <span className="font-data-sm text-data-sm text-on-surface font-mono">ATM CALL</span>
                  </div>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 font-mono">
                    <span className="font-label-xs text-label-xs text-on-surface-variant">STRIKE</span>
                    <span className="font-data-md text-data-md text-on-surface text-right">645.00</span>
                    <span className="font-label-xs text-label-xs text-on-surface-variant">DTE</span>
                    <span className="font-data-md text-data-md text-on-surface text-right">14</span>
                    <span className="font-label-xs text-label-xs text-primary/70 mt-1 pt-1 border-t border-outline-variant/50">
                      IV
                    </span>
                    <span className="font-data-md text-data-md text-primary mt-1 pt-1 border-t border-outline-variant/50 text-right">
                      24.8%
                    </span>
                  </div>
                </div>

                {/* Axis Labels */}
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 font-label-xs text-label-xs text-on-surface-variant tracking-widest uppercase font-mono">
                  Strike Price ($)
                </div>
                <div className="absolute top-1/2 right-6 -translate-y-1/2 rotate-90 font-label-xs text-label-xs text-on-surface-variant tracking-widest uppercase font-mono">
                  Time to Expiration (DTE)
                </div>
                <div className="absolute top-1/2 left-6 -translate-y-1/2 -rotate-90 font-label-xs text-label-xs text-primary/70 tracking-widest uppercase font-mono">
                  Implied Volatility (%)
                </div>
              </div>
            )}

            {/* Mode 2: Heatmap View */}
            {viewMode === 'HEATMAP' && (
              <div className="w-full h-full p-8 flex flex-col justify-center max-w-2xl">
                <h4 className="font-label-xs text-label-xs text-outline uppercase tracking-widest mb-4">
                  Strike vs DTE Implied Volatility Heatmap
                </h4>
                <div className="grid grid-cols-6 gap-1 bg-surface-container-lowest p-2 border border-outline-variant/30">
                  <div className="p-2 text-label-xs font-label-xs text-outline font-mono">DTE \ K</div>
                  {['620', '630', '645', '660', '670'].map((k) => (
                    <div key={k} className="p-2 text-center font-data-sm text-data-sm text-on-surface font-mono">
                      ${k}
                    </div>
                  ))}
                  {['7D', '14D', '30D', '45D'].map((dte) => (
                    <React.Fragment key={dte}>
                      <div className="p-2 font-data-sm text-data-sm text-on-surface-variant font-mono">{dte}</div>
                      <div className="p-2 bg-error/30 text-error text-center font-mono font-bold">28.4%</div>
                      <div className="p-2 bg-error/20 text-error text-center font-mono">26.1%</div>
                      <div className="p-2 bg-primary/20 text-primary text-center font-mono">24.8%</div>
                      <div className="p-2 bg-primary/10 text-on-surface text-center font-mono">22.4%</div>
                      <div className="p-2 bg-primary/10 text-on-surface text-center font-mono">21.8%</div>
                    </React.Fragment>
                  ))}
                </div>
              </div>
            )}

            {/* Mode 3: Volatility Smile View */}
            {viewMode === 'SMILE' && (
              <div className="w-full h-full p-8 flex flex-col items-center justify-center max-w-3xl relative">
                <h4 className="font-label-xs text-label-xs text-outline uppercase tracking-widest mb-4 self-start">
                  30D Implied Volatility Smile & Skew Curve
                </h4>
                <svg className="w-full h-64 border-b border-l border-outline-variant/30 p-4" viewBox="0 0 600 200">
                  {/* Grid */}
                  <line x1="0" y1="100" x2="600" y2="100" stroke="#192122" strokeDasharray="4 4" />
                  <line x1="300" y1="0" x2="300" y2="200" stroke="#3b494c" strokeWidth="1" />
                  {/* Smile Curve */}
                  <path
                    d="M 50,40 Q 250,160 300,150 T 550,80"
                    fill="none"
                    stroke="#00e5ff"
                    strokeWidth="3"
                  />
                  {/* Put Skew Highlight */}
                  <circle cx="150" cy="90" r="4" fill="#ffb4ab" />
                  <text x="160" y="85" fill="#ffb4ab" fontSize="11" fontFamily="JetBrains Mono">
                    25Δ Put (27.4%)
                  </text>
                  {/* ATM */}
                  <circle cx="300" cy="150" r="4" fill="#00daf3" />
                  <text x="310" y="145" fill="#00daf3" fontSize="11" fontFamily="JetBrains Mono">
                    ATM (23.1%)
                  </text>
                  {/* Call Skew */}
                  <circle cx="480" cy="100" r="4" fill="#cdbdff" />
                  <text x="490" y="95" fill="#cdbdff" fontSize="11" fontFamily="JetBrains Mono">
                    25Δ Call (21.8%)
                  </text>
                </svg>
              </div>
            )}
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
