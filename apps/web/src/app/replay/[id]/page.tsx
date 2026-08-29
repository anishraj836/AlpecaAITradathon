'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';

export default function DecisionReplayPage() {
  const params = useParams();
  const replayId = typeof params?.id === 'string' ? params.id : 'AFP-1024';

  const [currentTime, setCurrentTime] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const duration = 13; // 13 seconds

  const animationFrameRef = useRef<number | null>(null);
  const lastTimeRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isPlaying) {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      lastTimeRef.current = null;
      return;
    }

    const animate = (timestamp: number) => {
      if (!lastTimeRef.current) lastTimeRef.current = timestamp;
      const delta = (timestamp - lastTimeRef.current) / 1000;
      lastTimeRef.current = timestamp;

      setCurrentTime((prev) => {
        const next = prev + delta;
        if (next >= duration) {
          setIsPlaying(false);
          return duration;
        }
        return next;
      });

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, [isPlaying, duration]);

  const progressPercent = (currentTime / duration) * 100;
  const currentSecInt = Math.floor(currentTime);

  return (
    <div className="flex flex-col w-full h-[calc(100vh-4rem-8px)] relative rounded-sm border border-outline-variant/20 overflow-hidden bg-surface-container-low">
      {/* Header Context Strip */}
      <div className="flex items-center justify-between p-4 bg-surface-container/50 border-b border-outline-variant/30 shrink-0 select-none">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary-fixed text-[24px]">history</span>
            <h1 className="font-headline-md text-headline-md text-on-surface uppercase tracking-widest font-bold">
              Decision Replay
            </h1>
          </div>
          <div className="h-6 w-px bg-outline-variant/30" />
          <div className="flex items-center gap-3 font-mono">
            <span className="font-data-md text-data-md text-primary-fixed-dim bg-primary/10 px-2 py-1 rounded-sm border border-primary/20">
              #{replayId}
            </span>
            <span className="font-data-md text-data-md text-on-surface font-bold">SPY</span>
            <span className="font-data-sm text-data-sm text-on-surface-variant uppercase border border-outline-variant/30 px-2 py-0.5 rounded-sm">
              Iron Condor
            </span>
          </div>
        </div>
        <div className="flex items-center gap-6 font-mono text-xs">
          <div className="flex flex-col items-end">
            <span className="font-label-xs text-label-xs text-outline uppercase font-sans">
              Execution Timestamp
            </span>
            <span className="font-data-md text-data-md text-on-surface">2026-08-29 10:42:15 EST</span>
          </div>
          <div className="flex items-center gap-2 bg-surface-container-high px-3 py-1.5 rounded-sm border border-outline-variant/30 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-error animate-pulse" />
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-widest">
              Historical State
            </span>
          </div>
        </div>
      </div>

      {/* Main Viewport Area */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Telemetry Stream */}
        <div className="w-80 flex flex-col border-r border-outline-variant/20 bg-surface z-10 p-4 space-y-6 overflow-y-auto font-mono">
          <div className="border-b border-outline-variant/20 pb-2 flex items-center justify-between text-outline text-xs">
            <span className="font-label-xs uppercase font-sans">System Telemetry Stream</span>
            <span className="material-symbols-outlined text-[16px]">sensors</span>
          </div>

          {/* State 1: Market Context (T=0+) */}
          <div className={`transition-opacity duration-300 ${currentTime >= 0 ? 'opacity-100' : 'opacity-20'}`}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-1 h-3 bg-tertiary-container" />
              <h3 className="text-xs text-on-surface uppercase tracking-widest font-bold">
                T-00:00 Market Context
              </h3>
            </div>
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between p-2 bg-surface-container rounded-sm">
                <span className="text-on-surface-variant">VIX</span>
                <span className="text-tertiary-container font-bold">14.25</span>
              </div>
              <div className="flex justify-between p-2 bg-surface-container rounded-sm">
                <span className="text-on-surface-variant">SPY IV Rank</span>
                <span className="text-on-surface font-bold">32%</span>
              </div>
            </div>
          </div>

          {/* State 2: Generation (T=6+) */}
          <div className={`transition-opacity duration-300 ${currentTime >= 6 ? 'opacity-100' : 'opacity-20'}`}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-1 h-3 bg-secondary-container" />
              <h3 className="text-xs text-on-surface uppercase tracking-widest font-bold">
                T-00:06 Strategy Gen
              </h3>
            </div>
            <div className="p-2.5 bg-surface-container rounded-sm border-l-2 border-secondary-container text-xs">
              <div className="text-outline text-[10px]">CANDIDATE A (WINNER)</div>
              <div className="text-on-surface font-bold">Iron Condor (45 DTE)</div>
              <div className="text-on-surface-variant mt-0.5">PoP: 72% | Max Return: 15%</div>
            </div>
          </div>

          {/* State 3: Execution (T=13) */}
          <div className={`transition-opacity duration-300 ${currentTime >= 13 ? 'opacity-100' : 'opacity-20'}`}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-1 h-3 bg-primary-fixed" />
              <h3 className="text-xs text-on-surface uppercase tracking-widest font-bold">
                T-00:13 Paper Order
              </h3>
            </div>
            <div className="p-2.5 bg-surface-container-high rounded-sm border border-primary/30 text-xs">
              <div className="text-primary-fixed font-bold">ROUTED TO ALPACA</div>
              <div className="text-on-surface-variant mt-1 text-[11px]">Credit: $1.45 | Qty: 10</div>
            </div>
          </div>
        </div>

        {/* Center Dynamic Stage */}
        <div className="flex-1 flex flex-col items-center justify-center p-8 relative bg-surface-container-lowest">
          <div className="cockpit-grid absolute inset-0 opacity-20" />

          {/* Stage 1: Market Scan (0 - 5s) */}
          {currentTime < 6 && (
            <div className="flex flex-col items-center justify-center max-w-xl text-center z-10 animate-fade-in">
              <span className="material-symbols-outlined text-tertiary-container text-[48px] mb-2 animate-pulse">
                radar
              </span>
              <h2 className="font-headline-md text-headline-md text-on-surface font-bold mb-1">
                SCANNING VOLATILITY SURFACE
              </h2>
              <p className="font-body-sm text-body-sm text-outline font-mono">
                Evaluating IV smile across expirations. Inflection detected on SPY 45D Put wing.
              </p>
            </div>
          )}

          {/* Stage 2: Structuring Condor (6 - 12s) */}
          {currentTime >= 6 && currentTime < 13 && (
            <div className="flex flex-col items-center justify-center max-w-xl text-center z-10 animate-fade-in font-mono">
              <span className="material-symbols-outlined text-secondary-fixed text-[48px] mb-2">
                architecture
              </span>
              <h2 className="font-headline-md text-headline-md text-on-surface font-bold mb-1">
                STRUCTURING IRON CONDOR
              </h2>
              <div className="flex gap-4 mt-4">
                <span className="px-3 py-1 bg-surface-container border border-outline-variant/30 rounded-sm text-primary font-bold">
                  BUY 630P / SELL 640P
                </span>
                <span className="px-3 py-1 bg-surface-container border border-outline-variant/30 rounded-sm text-primary font-bold">
                  SELL 660C / BUY 670C
                </span>
              </div>
            </div>
          )}

          {/* Stage 3: Order Executed (13s) */}
          {currentTime >= 13 && (
            <div className="flex flex-col items-center justify-center text-center z-10 animate-fade-in font-mono">
              <div className="w-20 h-20 rounded-full bg-primary/10 border border-primary/30 flex items-center justify-center mb-4 shadow-glow-primary">
                <span className="material-symbols-outlined text-[42px] text-primary-fixed">check_circle</span>
              </div>
              <h2 className="font-display-lg text-display-lg text-on-surface font-bold mb-1">
                ORDER EXECUTED (ALPACA PAPER)
              </h2>
              <div className="flex gap-4 mt-4 text-xs">
                <div className="px-4 py-2 bg-surface-container border border-outline-variant/30 rounded-sm">
                  <span className="text-outline uppercase text-[10px] block">Fill Price</span>
                  <span className="text-primary-fixed font-bold text-sm">$1.45</span>
                </div>
                <div className="px-4 py-2 bg-surface-container border border-outline-variant/30 rounded-sm">
                  <span className="text-outline uppercase text-[10px] block">Max Profit</span>
                  <span className="text-primary-fixed-dim font-bold text-sm">$1,450.00</span>
                </div>
                <div className="px-4 py-2 bg-surface-container border border-outline-variant/30 rounded-sm">
                  <span className="text-outline uppercase text-[10px] block">Max Risk</span>
                  <span className="text-error font-bold text-sm">$8,550.00</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Timeline Scrubber Bottom Bar */}
      <div className="h-20 bg-surface-container-high border-t border-outline-variant/30 shrink-0 flex flex-col p-3 shadow-xl z-20 font-mono select-none">
        {/* Track */}
        <div
          onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const clickPct = (e.clientX - rect.left) / rect.width;
            setCurrentTime(clickPct * duration);
          }}
          className="flex-1 relative mb-2 flex items-center cursor-pointer group"
        >
          <div className="w-full h-1.5 bg-surface rounded-full overflow-hidden border border-outline-variant/20 relative">
            <div
              className="h-full bg-primary-fixed shadow-glow-primary transition-all duration-75"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between px-2">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsPlaying(!isPlaying)}
              className="w-8 h-8 flex items-center justify-center rounded-sm bg-primary text-on-primary hover:bg-primary-fixed transition-colors"
            >
              <span className="material-symbols-outlined text-[20px]">
                {isPlaying ? 'pause' : 'play_arrow'}
              </span>
            </button>
            <button
              type="button"
              onClick={() => setCurrentTime((t) => Math.min(t + 2, duration))}
              className="w-8 h-8 flex items-center justify-center rounded-sm border border-outline-variant/50 text-on-surface-variant hover:text-on-surface transition-colors"
            >
              <span className="material-symbols-outlined text-[20px]">skip_next</span>
            </button>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-primary-fixed">00:{currentSecInt.toString().padStart(2, '0')}</span>
            <span className="text-outline">/</span>
            <span className="text-on-surface-variant">00:13</span>
          </div>
        </div>
      </div>
    </div>
  );
}
