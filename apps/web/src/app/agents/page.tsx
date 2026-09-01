'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import {
  AgentFleetStatus,
  AgentLogEntry,
  AutonomousDaemonState,
  AutonomyLevel,
} from '@/types/voltron';

const ROLE_COLORS: Record<string, { badge: string; text: string; border: string; bg: string }> = {
  RESEARCHER: {
    badge: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    text: 'text-blue-400',
    border: 'border-blue-500/40',
    bg: 'bg-blue-500/5',
  },
  VOLATILITY_ANALYST: {
    badge: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
    text: 'text-cyan-400',
    border: 'border-cyan-500/40',
    bg: 'bg-cyan-500/5',
  },
  STRATEGY_SPECIALIST: {
    badge: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    text: 'text-purple-400',
    border: 'border-purple-500/40',
    bg: 'bg-purple-500/5',
  },
  RISK_CRITIC: {
    badge: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    text: 'text-amber-400',
    border: 'border-amber-500/40',
    bg: 'bg-amber-500/5',
  },
  AUTONOMOUS_DAEMON: {
    badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    text: 'text-emerald-400',
    border: 'border-emerald-500/40',
    bg: 'bg-emerald-500/5',
  },
};

const LEVEL_COLORS: Record<string, string> = {
  INFO: 'text-outline-variant',
  THINKING: 'text-primary font-mono',
  WARNING: 'text-amber-400',
  ERROR: 'text-error font-bold',
  SUCCESS: 'text-emerald-400 font-semibold',
  DISPATCH: 'text-cyan-400 font-bold bg-cyan-950/40 px-1 py-0.5 rounded',
};

export default function AgentsDashboardPage() {
  const [agents, setAgents] = useState<AgentFleetStatus[]>([]);
  const [daemon, setDaemon] = useState<AutonomousDaemonState | null>(null);
  const [logs, setLogs] = useState<AgentLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [roleFilter, setRoleFilter] = useState<string>('ALL');
  const [levelFilter, setLevelFilter] = useState<string>('ALL');
  const [searchLogQuery, setSearchLogQuery] = useState<string>('');
  const [newTickerInput, setNewTickerInput] = useState('');
  const [manualScanSymbol, setManualScanSymbol] = useState('PLTR');
  const [notification, setNotification] = useState<string | null>(null);

  const consoleBoxRef = useRef<HTMLDivElement>(null);

  // Load telemetry
  const fetchTelemetry = async () => {
    try {
      const data = await api.getAgentsStatus();
      setAgents(data.agents);
      setDaemon(data.daemon);
      setLogs(data.recentLogs);
    } catch (err) {
      console.warn('Failed to load agents status:', err);
    } finally {
      setLoading(false);
    }
  };

  // Poll telemetry every 2 seconds
  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleControl = async (action: 'PAUSE' | 'RESUME' | 'TRIGGER_SCAN' | 'SET_AUTONOMY' | 'SET_WATCHLIST' | 'SET_RATE_LIMIT_GUARD', payload?: any) => {
    setActionLoading(true);
    try {
      const updatedDaemon = await api.controlAutonomousDaemon({
        action,
        ...payload,
      });
      setDaemon(updatedDaemon);
      if (action === 'PAUSE') setNotification('⏸️ Autonomous worker loop paused.');
      else if (action === 'RESUME') setNotification('▶️ Autonomous worker loop resumed.');
      else if (action === 'TRIGGER_SCAN') setNotification(`⚡ Manual scan triggered for ${payload?.symbol || 'watchlist'}.`);
      else if (action === 'SET_AUTONOMY') setNotification(`🛡️ Autonomy level updated to ${payload?.autonomyLevel}.`);
      else if (action === 'SET_RATE_LIMIT_GUARD') setNotification(payload?.rateLimitGuardEnabled ? '🛡️ Rate-Limit Guard ENABLED (15 RPM Safe Mode).' : '⚡ Rate-Limit Guard DISABLED (Uncapped Turbo Mode).');
      else if (action === 'SET_WATCHLIST') setNotification('📋 Watchlist successfully updated.');
      setTimeout(() => setNotification(null), 4000);
      await fetchTelemetry();
    } catch (err: any) {
      console.error('Failed to dispatch control:', err);
      setNotification(`❌ Error: ${err?.message || 'Action failed'}`);
    } finally {
      setActionLoading(false);
    }
  };

  // Add Watchlist Symbol
  const handleAddTicker = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTickerInput.trim() || !daemon) return;
    const sym = newTickerInput.trim().toUpperCase();
    if (!daemon.watchlist.includes(sym)) {
      const nextList = [...daemon.watchlist, sym];
      await handleControl('SET_WATCHLIST', { watchlist: nextList });
    }
    setNewTickerInput('');
  };

  // Remove Watchlist Symbol
  const handleRemoveTicker = async (sym: string) => {
    if (!daemon) return;
    const nextList = daemon.watchlist.filter((s) => s !== sym);
    await handleControl('SET_WATCHLIST', { watchlist: nextList });
  };

  // Filter logs
  const filteredLogs = logs.filter((log) => {
    if (roleFilter !== 'ALL' && log.agentRole !== roleFilter) return false;
    if (levelFilter !== 'ALL' && log.level !== levelFilter) return false;
    if (searchLogQuery) {
      const q = searchLogQuery.toLowerCase();
      return (
        log.message.toLowerCase().includes(q) ||
        (log.symbol && log.symbol.toLowerCase().includes(q)) ||
        log.agentName.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="flex flex-col w-full h-full gap-container-gap pb-container-gap">
      {/* Toast Notification Banner */}
      {notification && (
        <div className="bg-surface-container-high border-2 border-primary/60 text-primary px-4 py-2.5 rounded-sm flex items-center justify-between font-mono text-xs shadow-lg animate-fade-in">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">info</span>
            <span className="font-bold">{notification}</span>
          </div>
          <button
            type="button"
            onClick={() => setNotification(null)}
            className="text-outline hover:text-on-surface p-1"
          >
            <span className="material-symbols-outlined text-[16px]">close</span>
          </button>
        </div>
      )}

      {/* Top Mission Control Header */}
      <div className="bg-surface-container rounded-sm border border-outline-variant/30 p-panel-padding shadow-md flex flex-col gap-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-sm bg-primary/10 border border-primary/30 flex items-center justify-center text-primary">
                <span className="material-symbols-outlined text-[24px]">smart_toy</span>
              </div>
              <div>
                <h1 className="font-headline-md text-headline-md text-on-surface font-bold tracking-tight">
                  Autonomous Multi-Agent Fleet
                </h1>
                <p className="font-body-sm text-body-sm text-on-surface-variant font-mono">
                  Live background daemon, multi-agent reasoning telemetry, and real-time execution console.
                </p>
              </div>
            </div>
          </div>

          {/* Master Daemon Controls */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Autonomy Level Switcher */}
            <div className="flex items-center bg-surface border border-outline-variant/40 rounded-sm p-0.5">
              {(['COPILOT', 'GUARDED_AUTONOMOUS', 'AUTOPILOT', 'UNCAPPED_AUTONOMOUS'] as AutonomyLevel[]).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => handleControl('SET_AUTONOMY', { autonomyLevel: mode })}
                  disabled={actionLoading}
                  className={`px-3 py-1 text-[11px] font-mono font-bold rounded-sm transition-all ${
                    daemon?.autonomyLevel === mode
                      ? mode === 'UNCAPPED_AUTONOMOUS'
                        ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-sm font-black'
                        : mode === 'AUTOPILOT'
                        ? 'bg-cyan-500 text-black shadow-sm'
                        : 'bg-primary text-on-primary shadow-sm'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  {mode === 'COPILOT'
                    ? 'COPILOT'
                    : mode === 'GUARDED_AUTONOMOUS'
                    ? 'GUARDED AUTO'
                    : mode === 'AUTOPILOT'
                    ? 'AUTOPILOT'
                    : '⚡ FREE TRADE (UNCAPPED)'}
                </button>
              ))}
            </div>

            {/* Pause / Resume Button */}
            <button
              type="button"
              onClick={() => handleControl(daemon?.isPaused ? 'RESUME' : 'PAUSE')}
              disabled={actionLoading}
              className={`px-3.5 py-1.5 rounded-sm font-mono text-xs font-bold flex items-center gap-1.5 transition-all shadow-xs ${
                daemon?.isPaused
                  ? 'bg-emerald-500 text-black hover:bg-emerald-400'
                  : 'bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30'
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">
                {daemon?.isPaused ? 'play_arrow' : 'pause'}
              </span>
              <span>{daemon?.isPaused ? 'RESUME DAEMON' : 'PAUSE DAEMON'}</span>
            </button>

            {/* Rate-Limit Capped Mode Toggle */}
            <button
              type="button"
              onClick={() => handleControl('SET_RATE_LIMIT_GUARD', { rateLimitGuardEnabled: !daemon?.rateLimitGuard })}
              disabled={actionLoading}
              title={
                daemon?.rateLimitGuard
                  ? "Rate-Limit Guard ACTIVE: Limits calls to 12 RPM, paces agent handoffs with delays, and caches 3-min sentiment to protect Google Free Tier quota (15 RPM / 500 RPD)."
                  : "Uncapped Turbo Mode: Full speed with zero inter-agent delays. Requires paid API key."
              }
              className={`px-3 py-1.5 rounded-sm font-mono text-xs font-bold flex items-center gap-1.5 transition-all border ${
                daemon?.rateLimitGuard
                  ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40 hover:bg-emerald-500/25 shadow-xs'
                  : 'bg-surface text-outline border-outline-variant/40 hover:text-on-surface hover:border-outline'
              }`}
            >
              <span className="material-symbols-outlined text-[15px] text-emerald-400">
                {daemon?.rateLimitGuard ? 'verified_user' : 'lock_open'}
              </span>
              <span>
                {daemon?.rateLimitGuard ? 'CAPPED MODE: ON (15 RPM SAFE)' : 'CAPPED MODE: OFF (UNCAPPED)'}
              </span>
            </button>

            {/* Trigger Immediate Scan */}
            <div className="flex items-center bg-surface border border-outline-variant/40 rounded-sm">
              <input
                type="text"
                value={manualScanSymbol}
                onChange={(e) => setManualScanSymbol(e.target.value.toUpperCase())}
                placeholder="PLTR"
                className="w-16 px-2 py-1 bg-transparent text-xs font-mono font-bold text-on-surface uppercase outline-none"
              />
              <button
                type="button"
                onClick={() => handleControl('TRIGGER_SCAN', { symbol: manualScanSymbol })}
                disabled={actionLoading}
                className="px-3 py-1 bg-primary text-on-primary hover:bg-primary-fixed-dim font-mono text-xs font-bold rounded-r-sm flex items-center gap-1 transition-colors"
              >
                <span className="material-symbols-outlined text-[14px]">bolt</span>
                <span>SCAN NOW</span>
              </button>
            </div>
          </div>
        </div>

        {/* Free Trading Active Banner */}
        {daemon?.autonomyLevel === 'UNCAPPED_AUTONOMOUS' && (
          <div className="bg-purple-950/40 border border-purple-500/40 px-3.5 py-2.5 rounded-sm flex items-center justify-between font-mono text-xs text-purple-200 shadow-sm animate-pulse">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-purple-400 text-[18px]">lock_open_right</span>
              <span>
                <strong>FREE TRADING ACTIVE:</strong> The autonomous fleet is trading unrestricted with <strong>zero upper bounds</strong> on investment budget, allocation, or position sizing caps.
              </span>
            </div>
            <span className="px-2 py-0.5 bg-purple-500/20 text-purple-300 text-[10px] font-bold rounded border border-purple-500/50 uppercase">
              Full Buying Power
            </span>
          </div>
        )}

        {/* Telemetry Metric Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 pt-3 border-t border-outline-variant/20">
          <div className="bg-surface p-2.5 rounded-sm border border-outline-variant/30 flex flex-col">
            <span className="text-[10px] font-mono text-outline uppercase">Fleet Status</span>
            <div className="flex items-center gap-1.5 mt-1">
              <div className={`w-2 h-2 rounded-full ${daemon?.isPaused ? 'bg-amber-400' : 'bg-emerald-400 animate-pulse'}`} />
              <span className="font-mono text-xs font-bold text-on-surface">
                {daemon?.isPaused ? 'PAUSED' : '4/4 ONLINE'}
              </span>
            </div>
          </div>

          <div className="bg-surface p-2.5 rounded-sm border border-outline-variant/30 flex flex-col">
            <span className="text-[10px] font-mono text-outline uppercase">Market Clock</span>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="material-symbols-outlined text-[14px] text-emerald-400">schedule</span>
              <span className="font-mono text-xs font-bold text-emerald-400">
                {daemon?.marketStatus || 'OPEN'} (US/EST)
              </span>
            </div>
          </div>

          <div className="bg-surface p-2.5 rounded-sm border border-outline-variant/30 flex flex-col">
            <span className="text-[10px] font-mono text-outline uppercase">Cycle Interval</span>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="font-mono text-xs font-bold text-primary">
                {daemon?.currentCycleSeconds || 0}s / {daemon?.cycleIntervalSeconds || 45}s
              </span>
            </div>
          </div>

          <div className="bg-surface p-2.5 rounded-sm border border-outline-variant/30 flex flex-col">
            <span className="text-[10px] font-mono text-outline uppercase">Cycles Run</span>
            <span className="font-mono text-xs font-bold text-on-surface mt-1">
              {daemon?.totalCyclesCompleted || 0} cycles
            </span>
          </div>

          <div className="bg-surface p-2.5 rounded-sm border border-cyan-500/30 flex flex-col">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-outline uppercase">Dispatched</span>
              <span className="material-symbols-outlined text-[13px] text-cyan-400">send</span>
            </div>
            <span className="font-mono text-xs font-bold text-cyan-400 mt-1">
              {daemon?.totalOrdersExecuted || 0} orders
            </span>
            <span className="text-[9px] font-mono text-outline mt-0.5">Alpaca Verified</span>
          </div>

          <div className="bg-surface p-2.5 rounded-sm border border-amber-500/30 flex flex-col">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-outline uppercase">Risk Rejections</span>
              <span className="material-symbols-outlined text-[13px] text-amber-400">shield</span>
            </div>
            <span className="font-mono text-xs font-bold text-amber-400 mt-1">
              {daemon?.totalOrdersRejected || 0} blocked
            </span>
            <span className="text-[9px] font-mono text-amber-300/80 mt-0.5">Capital Preserved</span>
          </div>

          <div className="bg-surface p-2.5 rounded-sm border border-outline-variant/30 flex flex-col">
            <span className="text-[10px] font-mono text-outline uppercase">Dislocations</span>
            <span className="font-mono text-xs font-bold text-purple-400 mt-1">
              {daemon?.totalDislocationsFound || 0} detected
            </span>
            <span className="text-[9px] font-mono text-outline mt-0.5">Quant MCP Scans</span>
          </div>

          <div className="bg-surface p-2.5 rounded-sm border border-emerald-500/30 flex flex-col">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono text-outline uppercase">API Consumption</span>
              <span className={`material-symbols-outlined text-[13px] ${(daemon?.estimatedRpm || 0) > 12 ? 'text-rose-400' : 'text-emerald-400'}`}>speed</span>
            </div>
            <div className="flex items-baseline gap-1 mt-1">
              <span className={`font-mono text-xs font-bold ${(daemon?.estimatedRpm || 0) > 12 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {daemon?.estimatedRpm || 0}
              </span>
              <span className="text-[10px] font-mono text-outline">/ {daemon?.rpmLimit || 15} RPM</span>
            </div>
            <span className="text-[9px] font-mono text-emerald-300/80 mt-0.5">
              {daemon?.rateLimitGuard ? '15 RPM Guard Active' : 'Uncapped'}
            </span>
          </div>
        </div>

        {/* Watchlist Strip */}
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-outline-variant/20">
          <span className="text-[11px] font-mono text-outline uppercase font-bold">
            Autonomous Scan Watchlist:
          </span>
          {daemon?.watchlist.map((sym) => (
            <div
              key={sym}
              className="flex items-center gap-1 px-2 py-0.5 bg-surface border border-outline-variant/30 rounded-sm font-mono text-xs font-bold text-primary"
            >
              <span>{sym}</span>
              <button
                type="button"
                onClick={() => handleRemoveTicker(sym)}
                className="text-outline hover:text-error transition-colors text-[10px] ml-0.5"
                title={`Remove ${sym}`}
              >
                ×
              </button>
            </div>
          ))}
          <form onSubmit={handleAddTicker} className="flex items-center gap-1">
            <input
              type="text"
              placeholder="+ Ticker"
              value={newTickerInput}
              onChange={(e) => setNewTickerInput(e.target.value.toUpperCase())}
              className="w-20 px-2 py-0.5 bg-surface border border-outline-variant/30 rounded-sm text-xs font-mono text-on-surface uppercase outline-none font-bold placeholder:text-outline"
            />
            <button
              type="submit"
              className="px-2 py-0.5 bg-primary/20 hover:bg-primary/30 text-primary rounded-sm text-xs font-mono font-bold"
            >
              ADD
            </button>
          </form>
        </div>
      </div>

      {/* Sequential Multi-Agent Pipeline Visualization */}
      <div className="bg-surface-container rounded-sm border border-outline-variant/30 p-panel-padding shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px] text-primary">account_tree</span>
            <h3 className="font-label-xs text-label-xs text-outline uppercase tracking-widest">
              Live Autonomous Pipeline Progression
            </h3>
          </div>
          <span className="font-mono text-[11px] text-on-surface-variant">
            Target: <strong className="text-primary">{agents[0]?.currentSymbol || 'PLTR'}</strong>
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
          {agents.map((agent, index) => {
            const styling = ROLE_COLORS[agent.role] || ROLE_COLORS.RESEARCHER;
            return (
              <div
                key={agent.id}
                className={`p-3 rounded-sm border ${styling.border} ${styling.bg} flex flex-col gap-1.5 relative overflow-hidden`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-[10px] text-outline font-bold">0{index + 1}.</span>
                    <span className={`font-mono text-xs font-bold ${styling.text}`}>
                      {agent.name.split(' ')[0]}
                    </span>
                  </div>
                  <span className={`px-1.5 py-0.5 text-[9px] font-mono font-bold rounded-sm border ${styling.badge}`}>
                    {agent.status}
                  </span>
                </div>

                <div className="flex items-center gap-1 text-[10px] font-mono text-outline mt-1">
                  <span className={`w-1.5 h-1.5 rounded-full ${agent.status === 'SCANNING' || agent.status === 'ACTIVE' ? 'bg-emerald-400 animate-pulse' : 'bg-outline'}`} />
                  <span>{agent.status === 'SCANNING' ? 'Executing' : 'Online'}</span>
                </div>

                <p className="text-[11px] font-mono text-on-surface-variant line-clamp-1">
                  {agent.currentTask}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Agent Fleet Detail Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-container-gap">
        {agents.map((agent) => {
          const styling = ROLE_COLORS[agent.role] || ROLE_COLORS.RESEARCHER;
          return (
            <div
              key={agent.id}
              className={`bg-surface-container rounded-sm border ${styling.border} p-panel-padding flex flex-col justify-between shadow-sm relative overflow-hidden group`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-sm border ${styling.border} ${styling.bg} ${styling.text}`}>
                    <span className="material-symbols-outlined text-[22px]">
                      {agent.role === 'RESEARCHER'
                        ? 'feed'
                        : agent.role === 'VOLATILITY_ANALYST'
                        ? 'monitoring'
                        : agent.role === 'STRATEGY_SPECIALIST'
                        ? 'architecture'
                        : 'shield'}
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-mono text-sm font-bold text-on-surface">
                        {agent.name}
                      </h3>
                      <span className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded-sm border ${styling.badge}`}>
                        {agent.status}
                      </span>
                    </div>
                    <span className="text-[10px] font-mono text-outline">
                      Engine: {agent.model}
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-[11px] font-mono text-cyan-400 font-bold">
                    {agent.status}
                  </span>
                  <div className="text-[10px] font-mono text-outline">
                    {agent.latencyMs > 0 ? `${agent.latencyMs}ms latency` : 'Active'}
                  </div>
                </div>
              </div>

              <div className="my-3 space-y-2">
                <div className="flex items-center justify-between text-[11px] font-mono text-on-surface-variant mb-1">
                  <span className="text-outline">Active Task:</span>
                  <span className="font-semibold text-primary">{agent.currentTask}</span>
                </div>

                <div className="bg-surface/80 p-2.5 rounded-sm border border-outline-variant/20 font-mono text-xs">
                  <span className="text-[10px] uppercase text-outline block mb-0.5">Latest Finding / Thesis:</span>
                  <span className="text-on-surface text-[11px] leading-relaxed">
                    {agent.lastFinding}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-outline-variant/20 font-mono text-[11px] text-outline">
                <span>Total Runs: <strong className="text-on-surface">{agent.successfulRuns}</strong></span>
                <span>Active Symbol: <strong className="text-primary">{agent.currentSymbol || 'SPY'}</strong></span>
                <span>Updated: <strong className="text-on-surface">{new Date(agent.lastActiveAt).toLocaleTimeString()}</strong></span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Live Agent Terminal Logs Console */}
      <div className="bg-surface-container rounded-sm border border-outline-variant/30 flex flex-col h-[460px] overflow-hidden shadow-md font-mono">
        {/* Terminal Header Bar */}
        <div className="flex flex-wrap items-center justify-between p-3 border-b border-outline-variant/30 bg-surface/90">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-3 rounded-full bg-error" />
              <div className="w-3 h-3 rounded-full bg-amber-400" />
              <div className="w-3 h-3 rounded-full bg-emerald-400" />
            </div>
            <span className="text-xs font-bold text-on-surface uppercase tracking-wider flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[16px] text-primary">terminal</span>
              Autonomous Agent Console Feed ({filteredLogs.length} events)
            </span>
          </div>

          {/* Filter Chips */}
          <div className="flex items-center gap-2">
            {/* Role Filter */}
            <div className="flex items-center bg-surface border border-outline-variant/30 rounded-sm p-0.5">
              {(['ALL', 'RESEARCHER', 'VOLATILITY_ANALYST', 'STRATEGY_SPECIALIST', 'RISK_CRITIC', 'AUTONOMOUS_DAEMON'] as const).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setRoleFilter(r)}
                  className={`px-2 py-0.5 text-[10px] font-bold rounded-sm transition-all ${
                    roleFilter === r
                      ? 'bg-primary text-on-primary'
                      : 'text-outline hover:text-on-surface'
                  }`}
                >
                  {r === 'ALL' ? 'ALL' : r.replace('_ANALYST', '').replace('STRATEGY_', '').replace('AUTONOMOUS_', '')}
                </button>
              ))}
            </div>

            {/* Level & Rejection Filter */}
            <div className="flex items-center bg-surface border border-outline-variant/30 rounded-sm p-0.5">
              {(['ALL', 'DISPATCH', 'WARNING', 'SUCCESS'] as const).map((lvl) => (
                <button
                  key={lvl}
                  type="button"
                  onClick={() => setLevelFilter(lvl)}
                  className={`px-2 py-0.5 text-[10px] font-bold rounded-sm transition-all ${
                    levelFilter === lvl
                      ? lvl === 'WARNING'
                        ? 'bg-amber-500 text-black font-bold'
                        : lvl === 'DISPATCH'
                        ? 'bg-cyan-500 text-black font-bold'
                        : 'bg-primary text-on-primary font-bold'
                      : 'text-outline hover:text-on-surface'
                  }`}
                >
                  {lvl === 'ALL' ? 'ALL' : lvl === 'WARNING' ? 'REJECTED' : lvl}
                </button>
              ))}
            </div>

            <div className="flex items-center bg-surface border border-outline-variant/30 rounded-sm px-2 py-0.5">
              <input
                type="text"
                placeholder="Search logs..."
                value={searchLogQuery}
                onChange={(e) => setSearchLogQuery(e.target.value)}
                className="w-28 bg-transparent text-[11px] text-on-surface outline-none placeholder:text-outline"
              />
            </div>

            <button
              type="button"
              onClick={() => {
                if (consoleBoxRef.current) {
                  consoleBoxRef.current.scrollTop = consoleBoxRef.current.scrollHeight;
                }
              }}
              className="px-2 py-0.5 rounded-sm text-[10px] font-bold border border-outline-variant/40 bg-surface text-outline hover:text-primary hover:border-primary/40 transition-colors flex items-center gap-1 cursor-pointer"
            >
              <span className="material-symbols-outlined text-[12px]">arrow_downward</span>
              <span>SCROLL TO BOTTOM</span>
            </button>
          </div>
        </div>

        {/* Monospace Scrolling Console Window */}
        <div
          ref={consoleBoxRef}
          className="flex-1 p-4 bg-[#0a0f18] text-[#c9d1d9] overflow-y-auto space-y-2 text-xs select-text"
        >
          {filteredLogs.length === 0 ? (
            <div className="text-outline text-center py-12">No logs matching filter criteria.</div>
          ) : (
            filteredLogs.map((log) => {
              const styling = ROLE_COLORS[log.agentRole] || ROLE_COLORS.RESEARCHER;
              const levelColor = LEVEL_COLORS[log.level] || 'text-outline-variant';
              return (
                <div key={log.id} className="flex items-start gap-2.5 hover:bg-white/5 p-1 rounded-sm transition-colors">
                  <span className="text-[#6e7681] text-[11px] select-none shrink-0 font-mono">
                    [{log.timestamp}]
                  </span>
                  <span className={`px-1.5 py-0.2 text-[9px] font-bold rounded-sm shrink-0 border ${styling.badge}`}>
                    {log.agentRole.replace('AUTONOMOUS_', '')}
                  </span>
                  <span className={`text-[10px] shrink-0 ${levelColor}`}>
                    [{log.level}]
                  </span>
                  {log.symbol && (
                    <span className="px-1.5 py-0.2 bg-primary/20 text-primary text-[10px] font-bold rounded-sm shrink-0">
                      {log.symbol}
                    </span>
                  )}
                  <span className="text-[#e6edf3] font-mono break-all leading-relaxed">
                    {log.message}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
