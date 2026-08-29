'use client';

import React, { useEffect, useState } from 'react';
import Image from 'next/image';
import { api } from '@/lib/api';
import { TelemetryStatus } from '@/types/voltron';
import { DEMO_TELEMETRY } from '@/fixtures/voltronFixtures';

export const HeaderTelemetryBar: React.FC = () => {
  const [telemetry, setTelemetry] = useState<TelemetryStatus>(DEMO_TELEMETRY);

  useEffect(() => {
    let isMounted = true;
    const fetchTelemetry = async () => {
      try {
        const data = await api.getTelemetry();
        if (isMounted) setTelemetry(data);
      } catch (err) {
        console.error('Failed to fetch telemetry:', err);
      }
    };

    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 10000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="fixed top-0 left-64 right-0 h-16 bg-surface-container/90 backdrop-blur-md border-b border-outline-variant/30 z-40 px-6 flex items-center justify-between shadow-sm select-none">
      {/* Left Market Metrics */}
      <div className="flex items-center gap-8">
        {/* Underlying Quote */}
        <div className="flex flex-col">
          <span className="font-label-xs text-label-xs text-outline uppercase tracking-tighter">
            Market Status ({telemetry.marketStatus})
          </span>
          <div className="flex items-center gap-2">
            <span className="font-data-md text-data-md text-on-surface font-bold">
              {telemetry.underlying}
            </span>
            <span className="font-data-md text-data-md text-primary-fixed-dim font-mono">
              ${telemetry.underlyingPrice.toFixed(2)}
            </span>
            <span className="font-data-sm text-data-sm text-tertiary-container font-mono">
              {telemetry.underlyingChangePct >= 0 ? '+' : ''}
              {telemetry.underlyingChangePct.toFixed(2)}%
            </span>
          </div>
        </div>

        <div className="h-8 w-px bg-outline-variant/30" />

        {/* Account Equity */}
        <div className="flex flex-col">
          <span className="font-label-xs text-label-xs text-outline uppercase tracking-tighter">
            Account Equity
          </span>
          <span className="font-data-md text-data-md text-primary-fixed font-mono font-bold">
            ${telemetry.accountEquity.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </span>
        </div>

        {/* Buying Power */}
        <div className="flex flex-col">
          <span className="font-label-xs text-label-xs text-outline uppercase tracking-tighter">
            Buying Power
          </span>
          <span className="font-data-md text-data-md text-on-surface font-mono">
            ${telemetry.buyingPower.toLocaleString('en-US', { minimumFractionDigits: 2 })}
          </span>
        </div>
      </div>

      {/* Right Connection Status & User Profile */}
      <div className="flex items-center gap-6">
        {/* Autonomous Mode Pill */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-surface-container-high rounded-sm border border-primary/30">
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          <span className="font-label-xs text-label-xs text-primary font-mono tracking-wider">
            AUTONOMOUS AGENT: ACTIVE
          </span>
        </div>

        {/* Alpaca Paper Status Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-container-high rounded-sm border border-outline-variant/30">
          <div className="w-2 h-2 rounded-full bg-primary-fixed-dim animate-pulse" />
          <span className="font-label-xs text-label-xs text-on-surface-variant font-mono tracking-wider">
            {telemetry.alpacaConnected
              ? telemetry.isPaper
                ? 'ALPACA CONNECTED (PAPER)'
                : 'ALPACA CONNECTED (LIVE)'
              : 'ALPACA DISCONNECTED'}
          </span>
        </div>

        {/* Timestamp */}
        <div className="flex flex-col items-end">
          <span className="font-label-xs text-label-xs text-outline uppercase font-mono">
            {telemetry.timestamp}
          </span>
        </div>

        {/* User profile & alerts */}
        <div className="flex items-center gap-4 border-l border-outline-variant/30 pl-6">
          <button className="relative text-on-surface-variant hover:text-on-surface transition-colors">
            <span className="material-symbols-outlined text-[20px]">notifications</span>
            <div className="absolute top-0 right-0 w-1.5 h-1.5 bg-error rounded-full" />
          </button>
          <div className="relative w-8 h-8 rounded-full overflow-hidden border border-outline-variant">
            <Image
              src="/assets/avatar.png"
              alt="Trader Profile"
              width={32}
              height={32}
              className="object-cover"
            />
          </div>
        </div>
      </div>
    </header>
  );
};
