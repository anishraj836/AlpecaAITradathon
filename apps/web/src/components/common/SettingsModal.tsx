"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { AutonomyLevel, SystemSettings } from "@/types/voltron";
import { 
  X, 
  CheckCircle2, 
  AlertTriangle, 
  Cpu, 
  ShieldCheck, 
  Zap, 
  RefreshCw, 
  Key, 
  Radio, 
  Activity,
  ChevronRight
} from "lucide-react";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSettingsUpdated?: (settings: SystemSettings) => void;
}

const PROVIDER_OPTIONS = [
  { id: "gemini", name: "Google Gemini", desc: "Low-latency multimodal reasoning (Free Tier)", defaultModel: "gemini-3.5-flash-lite" },
  { id: "openai", name: "OpenAI", desc: "GPT-4o / GPT-4o-mini / o3-mini models", defaultModel: "gpt-4o-mini" },
  { id: "groq", name: "Groq Cloud LPU", desc: "Ultra-fast 600 tok/sec LPUs (Free Tier)", defaultModel: "llama-3.3-70b-versatile" },
  { id: "anthropic", name: "Anthropic Claude", desc: "Claude 3.5 Sonnet / Haiku reasoning", defaultModel: "claude-3-5-haiku-20241022" },
  { id: "deepseek", name: "DeepSeek", desc: "DeepSeek-V3 and DeepSeek-R1", defaultModel: "deepseek-chat" },
  { id: "ollama", name: "Local Ollama", desc: "100% Offline GPU/Mac inference ($0.00)", defaultModel: "llama3.2:3b" },
];

const AUTONOMY_MODES: Array<{
  level: AutonomyLevel;
  title: string;
  badge: string;
  badgeColor: string;
  description: string;
  governance: string;
}> = [
  {
    level: "COPILOT",
    title: "Level 1: Copilot (Advisory)",
    badge: "Human-In-The-Loop",
    badgeColor: "border-amber-500/40 text-amber-400 bg-amber-500/10",
    description: "AI generates trades and stress-tests; execution safely halts in the Decision Room for manual 1-click human sign-off.",
    governance: "Mandatory Human Approval on 100% of orders.",
  },
  {
    level: "GUARDED_AUTONOMOUS",
    title: "Level 2: Guarded Autonomous",
    badge: "Default Demo Mode",
    badgeColor: "border-emerald-500/40 text-emerald-400 bg-emerald-500/10",
    description: "Agent executes approved trades directly to Alpaca ONLY if all deterministic quantitative risk gates pass 100%.",
    governance: "Fails closed to Decision Room if LLM is degraded or risk fails.",
  },
  {
    level: "AUTOPILOT",
    title: "Level 3: Portfolio Autopilot",
    badge: "Continuous Agent",
    badgeColor: "border-cyan-500/40 text-cyan-400 bg-cyan-500/10",
    description: "Full continuous scanning and portfolio delta-hedging with active kill-switch and portfolio margin boundaries.",
    governance: "Circuit-breaker stops on 2% intraday drawdown.",
  },
];

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  onSettingsUpdated,
}) => {
  const [provider, setProvider] = useState<string>("gemini");
  const [model, setModel] = useState<string>("gemini-3.5-flash-lite");
  const [apiKey, setApiKey] = useState<string>("");
  const [autonomyLevel, setAutonomyLevel] = useState<AutonomyLevel>("GUARDED_AUTONOMOUS");
  const [isMaskedKeyConfigured, setIsMaskedKeyConfigured] = useState<boolean>(false);
  
  const [loading, setLoading] = useState<boolean>(false);
  const [testingConnection, setTestingConnection] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; latencyMs?: number } | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  useEffect(() => {
    if (isOpen) {
      setTestResult(null);
      setSaveSuccess(false);
      api.getSettings()
        .then((s) => {
          setProvider(s.llmProvider || "gemini");
          setModel(s.llmModel || "gemini-3.5-flash-lite");
          setAutonomyLevel(s.autonomyLevel || "GUARDED_AUTONOMOUS");
          setIsMaskedKeyConfigured(s.isApiKeyConfigured);
        })
        .catch(() => {});
    }
  }, [isOpen]);

  const handleProviderChange = (newProv: string) => {
    setProvider(newProv);
    const found = PROVIDER_OPTIONS.find((p) => p.id === newProv);
    if (found) {
      setModel(found.defaultModel);
    }
    setTestResult(null);
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setTestResult(null);
    try {
      const res = await api.testLlmConnection({
        provider,
        model,
        apiKey: apiKey || undefined,
      });
      setTestResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Network error testing LLM provider";
      setTestResult({
        success: false,
        message: msg,
      });
    } finally {
      setTestingConnection(false);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const updated = await api.updateSettings({
        llmProvider: provider,
        llmModel: model,
        apiKey: apiKey || undefined,
        autonomyLevel,
      });
      setSaveSuccess(true);
      if (onSettingsUpdated) {
        onSettingsUpdated(updated);
      }
      setTimeout(() => {
        setSaveSuccess(false);
        onClose();
      }, 900);
    } catch (err) {
      console.error("Failed to save settings", err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-zinc-950/95 border border-zinc-800 rounded-xl shadow-2xl shadow-cyan-950/20 overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800/80 bg-zinc-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
                AI Provider & Autonomy Governance
              </h2>
              <p className="text-xs text-zinc-400">
                Configure active reasoning LLMs, API keys, and autonomous execution policies
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6 text-sm">
          
          {/* 1. LLM Provider Selector */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
              Active LLM Reasoning Engine
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
              {PROVIDER_OPTIONS.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => handleProviderChange(p.id)}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    provider === p.id
                      ? "border-cyan-500 bg-cyan-950/20 text-cyan-200 shadow-sm shadow-cyan-500/10"
                      : "border-zinc-800 bg-zinc-900/40 text-zinc-300 hover:border-zinc-700 hover:bg-zinc-900"
                  }`}
                >
                  <div className="font-medium text-xs flex items-center justify-between">
                    {p.name}
                    {provider === p.id && <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />}
                  </div>
                  <div className="text-[10px] text-zinc-500 mt-1 line-clamp-1">
                    {p.desc}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* 2. Model & API Key Inputs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-zinc-900/30 p-4 rounded-lg border border-zinc-800/60">
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1.5">
                Model Identifier
              </label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-zinc-950 border border-zinc-700/80 rounded-md text-zinc-100 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 font-mono"
                placeholder="e.g. gemini-3.5-flash-lite"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-medium text-zinc-300 flex items-center gap-1.5">
                  <Key className="w-3 h-3 text-zinc-400" /> API Key
                </label>
                {isMaskedKeyConfigured && !apiKey && (
                  <span className="text-[10px] text-emerald-400 font-mono bg-emerald-950/30 px-1.5 py-0.5 rounded border border-emerald-500/20">
                    ACTIVE IN ENV
                  </span>
                )}
              </div>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-zinc-950 border border-zinc-700/80 rounded-md text-zinc-100 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 font-mono"
                placeholder={isMaskedKeyConfigured ? "•••••••••••••••••••• (Configured)" : "Paste API key (optional if in .env)"}
              />
            </div>

            {/* Test Connection Button & Result */}
            <div className="sm:col-span-2 pt-1 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={testingConnection}
                className="px-3 py-1.5 text-xs font-medium rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 flex items-center gap-2 transition-colors disabled:opacity-50"
              >
                {testingConnection ? (
                  <RefreshCw className="w-3 h-3 animate-spin text-cyan-400" />
                ) : (
                  <Activity className="w-3 h-3 text-cyan-400" />
                )}
                {testingConnection ? "Testing Ping..." : "Test Connection"}
              </button>

              {testResult && (
                <div className={`text-xs px-2.5 py-1 rounded flex items-center gap-1.5 ${
                  testResult.success 
                    ? "bg-emerald-950/40 text-emerald-300 border border-emerald-500/30" 
                    : "bg-rose-950/40 text-rose-300 border border-rose-500/30"
                }`}>
                  {testResult.success ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  ) : (
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                  )}
                  <span className="line-clamp-1">{testResult.message}</span>
                </div>
              )}
            </div>
          </div>

          {/* 3. Autonomy Spectrum Mode */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-2">
              Execution Autonomy Spectrum
            </label>
            <div className="space-y-2.5">
              {AUTONOMY_MODES.map((m) => (
                <div
                  key={m.level}
                  onClick={() => setAutonomyLevel(m.level)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    autonomyLevel === m.level
                      ? "border-cyan-500 bg-cyan-950/15 shadow-sm shadow-cyan-500/10"
                      : "border-zinc-800 bg-zinc-900/30 hover:border-zinc-700"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <div className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center ${
                        autonomyLevel === m.level ? "border-cyan-400 bg-cyan-500" : "border-zinc-600"
                      }`}>
                        {autonomyLevel === m.level && <div className="w-1.5 h-1.5 rounded-full bg-black" />}
                      </div>
                      <span className="font-semibold text-xs text-zinc-100">{m.title}</span>
                    </div>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${m.badgeColor}`}>
                      {m.badge}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-400 pl-5.5 leading-relaxed">
                    {m.description}
                  </p>
                  <div className="mt-1.5 pl-5.5 text-[10px] text-zinc-500 flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3 text-cyan-400/80" />
                    <span>Governance: {m.governance}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-zinc-800/80 bg-zinc-900/40">
          <div className="text-[11px] text-zinc-500 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Fail-Safe: Degraded LLM automatically demotes to Copilot</span>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 text-xs font-medium rounded-md text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={loading}
              className="px-4 py-1.5 text-xs font-semibold rounded-md bg-cyan-500 hover:bg-cyan-400 text-zinc-950 shadow-sm shadow-cyan-500/20 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {saveSuccess ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" /> Applied!
                </>
              ) : loading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Saving...
                </>
              ) : (
                <>
                  <Zap className="w-3.5 h-3.5" /> Save & Apply
                </>
              )}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
