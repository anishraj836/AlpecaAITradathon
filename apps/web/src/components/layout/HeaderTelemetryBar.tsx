'use client';

import React, { useEffect, useState } from 'react';
import Image from 'next/image';
import { api } from '@/lib/api';
import { TelemetryStatus, SystemSettings, AutonomyLevel } from '@/types/voltron';
import { SettingsModal } from '@/components/common/SettingsModal';
import { Settings, Cpu, ShieldCheck, Zap } from 'lucide-react';

export const HeaderTelemetryBar: React.FC = () => {
  const [telemetry, setTelemetry] = useState<TelemetryStatus | null>(null);
  const [systemSettings, setSystemSettings] = useState<SystemSettings | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);

  const fetchSettings = async () => {
    try {
      const s = await api.getSettings();
      setSystemSettings(s);
    } catch {
      // Ignore if backend booting
    }
  };

  useEffect(() => {
    let isMounted = true;

    // Fast-hydrate from session cache to prevent any visual jump on page refresh
    if (typeof window !== 'undefined') {
      try {
        const cached = sessionStorage.getItem('voltron_telemetry_cache');
        if (cached) {
          const parsed = JSON.parse(cached);
          if (parsed && parsed.underlying) {
            setTelemetry(parsed);
          }
        }
      } catch {
        // Ignore JSON parse errors
      }
    }

    const fetchTelemetry = async () => {
      try {
        const data = await api.getTelemetry();
        if (isMounted) {
          setTelemetry(data);
          if (typeof window !== 'undefined') {
            sessionStorage.setItem('voltron_telemetry_cache', JSON.stringify(data));
          }
        }
      } catch (err) {
        console.error('Failed to fetch telemetry:', err);
      }
    };

    fetchTelemetry();
    fetchSettings();
    const interval = setInterval(fetchTelemetry, 10000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const getAutonomyBadge = (level: AutonomyLevel = 'GUARDED_AUTONOMOUS') => {
    switch (level) {
      case 'COPILOT':
        return {
          label: 'MODE: COPILOT (HITL)',
          color: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
          dot: 'bg-amber-400',
        };
      case 'AUTOPILOT':
        return {
          label: 'MODE: AUTOPILOT',
          color: 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400',
          dot: 'bg-cyan-400',
        };
      case 'GUARDED_AUTONOMOUS':
      default:
        return {
          label: 'MODE: GUARDED AUTO',
          color: 'bg-primary/10 border-primary/30 text-primary',
          dot: 'bg-primary',
        };
    }
  };

  const autonomyBadge = getAutonomyBadge(systemSettings?.autonomyLevel);

  return (
    <>
      <header className="fixed top-0 left-64 right-0 h-16 bg-surface-container/90 backdrop-blur-md border-b border-outline-variant/30 z-40 px-6 flex items-center justify-between shadow-sm select-none">
        {/* Left Market Metrics */}
        {!telemetry ? (
          <div className="flex items-center gap-3 text-xs font-mono text-outline">
            <span className="w-2 h-2 rounded-full bg-primary animate-ping" />
            <span className="tracking-wide">Connecting to Alpaca Live Market Stream...</span>
          </div>
        ) : (
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
        )}

        {/* Right Connection Status, Autonomy Mode & Settings */}
        <div className="flex items-center gap-4">
          {/* Interactive Autonomy Mode Badge */}
          <button
            type="button"
            onClick={() => setIsSettingsOpen(true)}
            className={`hidden md:flex items-center gap-2 px-3 py-1.5 rounded-sm border transition-all hover:brightness-110 cursor-pointer ${autonomyBadge.color}`}
            title="Click to configure Autonomy Level"
          >
            <div className={`w-2 h-2 rounded-full ${autonomyBadge.dot} animate-pulse`} />
            <span className="font-label-xs text-label-xs font-mono tracking-wider font-semibold">
              {autonomyBadge.label}
            </span>
          </button>

          {/* Active LLM Provider Button */}
          <button
            type="button"
            onClick={() => setIsSettingsOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 bg-surface-container-high rounded-sm border border-outline-variant/40 hover:border-cyan-500/50 hover:bg-zinc-800/80 transition-all text-on-surface-variant hover:text-zinc-100"
          >
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span className="font-label-xs text-label-xs font-mono tracking-wider">
              {systemSettings?.llmProvider ? `${systemSettings.llmProvider.toUpperCase()}` : 'LLM: ACTIVE'}
            </span>
            <Settings className="w-3 h-3 text-outline" />
          </button>

          {/* Alpaca Paper Status Pill */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-surface-container-high rounded-sm border border-outline-variant/30">
            <div className="w-2 h-2 rounded-full bg-primary-fixed-dim animate-pulse" />
            <span className="font-label-xs text-label-xs text-on-surface-variant font-mono tracking-wider">
              {telemetry?.alpacaConnected
                ? telemetry.isPaper
                  ? 'ALPACA PAPER'
                  : 'ALPACA LIVE'
                : telemetry === null
                ? 'CONNECTING...'
                : 'ALPACA DISCONNECTED'}
            </span>
          </div>

          {/* User profile */}
          <div className="flex items-center gap-3 border-l border-outline-variant/30 pl-4">
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

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSettingsUpdated={(s) => setSystemSettings(s)}
      />
    </>
  );
};
