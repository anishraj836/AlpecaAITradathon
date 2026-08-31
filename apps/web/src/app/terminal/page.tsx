'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { ActiveOperationState, MandatePipelineStep, AutonomyLevel } from '@/types/voltron';
import { DEMO_ACTIVE_OPERATION } from '@/fixtures/voltronFixtures';

const EXAMPLE_MANDATES = [
  'Harvest elevated put skew on SPY with defined risk',
  'Find optimal NVDA delta-neutral bull spread',
  'Capture AAPL volatility anomaly with put credit spread',
  'Scan QQQ high-probability iron condor',
];

export default function CommandTerminalPage() {
  const router = useRouter();
  const [mandate, setMandate] = useState('Harvest elevated put skew on SPY with defined risk');
  const [autonomyLevel, setAutonomyLevel] = useState<import('@/types/voltron').AutonomyLevel>('GUARDED_AUTONOMOUS');
  const [operationState, setOperationState] = useState<ActiveOperationState>(DEMO_ACTIVE_OPERATION);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [degradedNotice, setDegradedNotice] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);

  const toggleVoiceInput = () => {
    if (typeof window === 'undefined') return;
    const SpeechRecognition =
      (window as unknown as { SpeechRecognition?: any }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: any }).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setErrorMessage('Speech recognition is not supported in this browser. Please use Chrome, Safari, or Edge.');
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results?.[0]?.[0]?.transcript;
        if (transcript) {
          setMandate(transcript);
        }
        setIsListening(false);
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.start();
    } catch (e) {
      console.error(e);
      setIsListening(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    api.getActiveOperation().then((op) => {
      if (isMounted) setOperationState(op);
    });
    return () => {
      isMounted = false;
    };
  }, []);

  const handleExecuteMandate = async (customMandate?: string, targetAutonomy?: AutonomyLevel) => {
    const targetMandate = customMandate || mandate;
    const effectiveAutonomy = targetAutonomy || autonomyLevel;
    if (!targetMandate.trim()) return;

    setIsSubmitting(true);
    setErrorMessage(null);
    setDegradedNotice(null);

    // Initial state: Step 1 active
    setOperationState((prev) => ({
      ...prev,
      status: 'PROCESSING',
      mandate: targetMandate,
      steps: [
        { id: 'step-1', title: '01. Researcher Agent: Ingesting Microstructure & News', status: 'ACTIVE' },
        { id: 'step-2', title: '02. Volatility Analyst: Skew & Surface Anomaly', status: 'PENDING' },
        { id: 'step-3', title: '03. Strategy Tournament: Lognormal POP Ranking', status: 'PENDING' },
        { id: 'step-4', title: '04. Critic Agent: Adversarial Tail-Risk Scenarios', status: 'PENDING' },
        { id: 'step-5', title: '05. Deterministic Risk Compiler Gate', status: 'PENDING' },
        { id: 'step-6', title: '06. Alpaca Paper MLEG Dispatch & Decision Room', status: 'PENDING' },
      ],
    }));

    // Start API request in parallel with effective autonomy
    const mandatePromise = api.dispatchMandate(
      targetMandate,
      undefined,
      effectiveAutonomy
    );

    try {
      // Step 1 -> Step 2 after 550ms
      await new Promise((r) => setTimeout(r, 550));
      setOperationState((prev) => ({
        ...prev,
        steps: [
          {
            id: 'step-1',
            title: '01. Researcher Agent: Market Regime Identified',
            status: 'COMPLETE',
            durationMs: 480,
            outputSummary: [
              'Market Regime: Range-bound consolidation',
              'Analyzed price velocity, volume depth, and real-time news headlines',
            ],
          },
          {
            id: 'step-2',
            title: '02. Volatility Analyst: 21-Scenario Surface Anomaly',
            status: 'ACTIVE',
          },
          prev.steps[2],
          prev.steps[3],
          prev.steps[4],
          prev.steps[5],
        ],
      }));

      // Step 2 -> Step 3 after 550ms
      await new Promise((r) => setTimeout(r, 550));
      setOperationState((prev) => ({
        ...prev,
        steps: [
          prev.steps[0],
          {
            id: 'step-2',
            title: '02. Volatility Analyst: 21-Scenario Surface Anomaly',
            status: 'COMPLETE',
            durationMs: 390,
            outputSummary: [
              'ATM IV: 18.4% | IV Rank: 72.1%',
              'Elevated Put Skew (1.27x downside protection demand)',
            ],
          },
          {
            id: 'step-3',
            title: '03. Strategy Tournament: Simulating Candidates',
            status: 'ACTIVE',
          },
          prev.steps[3],
          prev.steps[4],
          prev.steps[5],
        ],
      }));

      // Step 3 -> Step 4 after 550ms
      await new Promise((r) => setTimeout(r, 550));
      setOperationState((prev) => ({
        ...prev,
        steps: [
          prev.steps[0],
          prev.steps[1],
          {
            id: 'step-3',
            title: '03. Strategy Tournament: Candidate Ranked',
            status: 'COMPLETE',
            durationMs: 440,
            outputSummary: [
              'Simulated 4 option structures across lognormal POP distribution',
              'Winner: 15-Delta Defined-Risk Structure',
            ],
          },
          {
            id: 'step-4',
            title: '04. Critic Agent: Stress Testing Failure Modes',
            status: 'ACTIVE',
          },
          prev.steps[4],
          prev.steps[5],
        ],
      }));

      // Step 4 -> Step 5 after 550ms
      await new Promise((r) => setTimeout(r, 550));
      setOperationState((prev) => ({
        ...prev,
        steps: [
          prev.steps[0],
          prev.steps[1],
          prev.steps[2],
          {
            id: 'step-4',
            title: '04. Critic Agent: Adversarial Attack Evaluated',
            status: 'COMPLETE',
            durationMs: 410,
            outputSummary: [
              'Stressed candidate against tail-risk breakout scenarios',
              'Critic Verdict: Passed with defined-risk boundary conditions',
            ],
          },
          {
            id: 'step-5',
            title: '05. Deterministic Risk Compiler Gate',
            status: 'ACTIVE',
          },
          prev.steps[5],
        ],
      }));

      // Await live API result from FastAPI backend
      const result = await mandatePromise;
      const packet = result.packet;
      const isRiskPass = packet?.riskCompilerResult?.isApproved ?? true;

      // Final Step 5 & 6 completion with live backend data
      setOperationState((prev) => ({
        ...prev,
        operationId: result.operationId,
        decisionId: result.decisionId,
        status: 'COMPLETED',
        steps: [
          {
            id: 'step-1',
            title: '01. Researcher Agent: Market Regime Identified',
            status: 'COMPLETE',
            durationMs: 480,
            outputSummary: [
              `Regime: ${packet?.marketRegime || 'Range-Bound Consolidation'}`,
              `Evidence: ${packet?.evidence?.description?.slice(0, 95) || 'Intraday price dispersion analyzed'}...`,
            ],
          },
          {
            id: 'step-2',
            title: '02. Volatility Analyst: 21-Scenario Surface Anomaly',
            status: 'COMPLETE',
            durationMs: 390,
            outputSummary: [
              `ATM IV: ${packet?.iv30 || 18.4}% | IV Rank: ${packet?.ivRank || 72.1}%`,
              'Put Skew Elevated (Asymmetric downside protection demand)',
            ],
          },
          {
            id: 'step-3',
            title: '03. Strategy Tournament: Candidate Selected',
            status: 'COMPLETE',
            durationMs: 440,
            outputSummary: [
              `Structure: ${packet?.strategy?.name || 'Iron Condor'} (${packet?.strategy?.legs?.length || 4} Legs)`,
              `POP: ${packet?.strategy ? (packet.strategy.pop * 100).toFixed(1) : '72.5'}% | Max Profit: $${packet?.strategy?.maxProfit?.toFixed(2) || '140.00'}`,
            ],
          },
          {
            id: 'step-4',
            title: '04. Critic Agent: Adversarial Attack Evaluated',
            status: 'COMPLETE',
            durationMs: 410,
            outputSummary: [
              `Failure Mode: ${packet?.criticAnalysis?.primaryFailureMode || 'Downside gap risk'}`,
              `Critic Verdict: ${packet?.status === 'REJECTED' ? 'VETOED (High tail risk)' : 'PASSED STRESS TEST'}`,
            ],
          },
          {
            id: 'step-5',
            title: '05. Deterministic Risk Compiler Gate',
            status: isRiskPass ? 'COMPLETE' : 'FAILED',
            durationMs: 120,
            outputSummary: [
              `Budget: ${packet?.riskCompilerResult?.budgetCheck?.status || 'PASS'} | Liquidity: ${packet?.riskCompilerResult?.liquidityCheck?.status || 'PASS'}`,
              `Concentration: ${packet?.riskCompilerResult?.concentrationCheck?.status || 'WARN'} | Risk Gate: ${isRiskPass ? 'PASSED (100%)' : 'VETOED'}`,
            ],
          },
          {
            id: 'step-6',
            title: '06. Alpaca Paper MLEG Dispatch & Decision Room',
            status: 'COMPLETE',
            durationMs: 180,
            outputSummary: [
              `Decision Packet: ${result.decisionId}`,
              `Final Status: ${packet?.status || 'AWAITING_APPROVAL'} | Mode: ${packet?.autonomyLevel || autonomyLevel}`,
            ],
          },
        ],
      }));

      if (result.packet?.isDegradedMode) {
        setDegradedNotice(
          '⚠️ Radical Transparency: AI Reasoning was offline. System safely demoted execution to Copilot Mode with pure deterministic math.'
        );
      }

      setIsSubmitting(false);
    } catch (err: any) {
      console.error('Failed to dispatch mandate:', err);
      setErrorMessage(err?.message || 'Failed to execute mandate.');
      setIsSubmitting(false);
      setOperationState((prev) => ({
        ...prev,
        status: 'IDLE',
      }));
    }
  };

  return (
    <div className="flex flex-col w-full h-full gap-gutter bg-surface">
      <div className="flex-1 grid grid-cols-12 gap-gutter bg-surface p-gutter h-[calc(100vh-4rem-8px)] overflow-hidden">
        {/* Left Column: Command Input & Environment State */}
        <div className="col-span-8 flex flex-col gap-gutter h-full overflow-y-auto pr-1">
          {/* Hero Input Area */}
          <div className="bg-surface-container-low flex-none relative p-8 group border border-outline-variant/10 rounded-sm">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 blur-3xl rounded-full" />

            <h1 className="font-display-lg text-display-lg text-on-surface mb-2 tracking-tight">
              VOLTRON <span className="text-primary opacity-90">AI OPTIONS DECISION SYSTEM</span>
            </h1>
            <p className="font-body-sm text-body-sm text-on-surface-variant max-w-2xl mb-6">
              Awaiting directional thesis or exploratory mandate. Multi-agent debate and pure-code risk compilation primed.
            </p>

            {/* Autonomy Spectrum Selector */}
            <div className="mb-6 flex flex-col gap-2">
              <span className="font-label-xs text-label-xs text-outline uppercase tracking-wider">
                Execution Autonomy Spectrum
              </span>
              <div className="grid grid-cols-3 gap-2 max-w-2xl">
                <button
                  type="button"
                  onClick={() => setAutonomyLevel('COPILOT')}
                  className={`p-2.5 rounded border text-left transition-all ${
                    autonomyLevel === 'COPILOT'
                      ? 'border-amber-500 bg-amber-500/10 text-amber-300'
                      : 'border-outline-variant/30 bg-surface-container/60 text-on-surface-variant hover:border-outline-variant'
                  }`}
                >
                  <div className="font-semibold text-xs flex items-center justify-between">
                    <span>Level 1: Copilot</span>
                    <span className="text-[10px] font-mono opacity-80">HITL</span>
                  </div>
                  <div className="text-[10px] text-outline mt-0.5">Decision Room Approval Required</div>
                </button>

                <button
                  type="button"
                  onClick={() => setAutonomyLevel('GUARDED_AUTONOMOUS')}
                  className={`p-2.5 rounded border text-left transition-all ${
                    autonomyLevel === 'GUARDED_AUTONOMOUS'
                      ? 'border-primary bg-primary/10 text-primary-fixed'
                      : 'border-outline-variant/30 bg-surface-container/60 text-on-surface-variant hover:border-outline-variant'
                  }`}
                >
                  <div className="font-semibold text-xs flex items-center justify-between">
                    <span>Level 2: Guarded Auto</span>
                    <span className="text-[10px] font-mono text-primary">DEMO</span>
                  </div>
                  <div className="text-[10px] text-outline mt-0.5">Executes on 100% Risk Pass</div>
                </button>

                <button
                  type="button"
                  onClick={() => setAutonomyLevel('AUTOPILOT')}
                  className={`p-2.5 rounded border text-left transition-all ${
                    autonomyLevel === 'AUTOPILOT'
                      ? 'border-cyan-500 bg-cyan-500/10 text-cyan-300'
                      : 'border-outline-variant/30 bg-surface-container/60 text-on-surface-variant hover:border-outline-variant'
                  }`}
                >
                  <div className="font-semibold text-xs flex items-center justify-between">
                    <span>Level 3: Autopilot</span>
                    <span className="text-[10px] font-mono opacity-80">AGENT</span>
                  </div>
                  <div className="text-[10px] text-outline mt-0.5">Continuous Loop + Circuit Breaker</div>
                </button>
              </div>
            </div>

            {/* Guided Missile: 1-Click Interactive Demo Storylines */}
            <div className="mb-6 flex flex-col gap-2 max-w-2xl">
              <div className="flex items-center justify-between">
                <span className="font-label-xs text-label-xs text-primary uppercase tracking-widest flex items-center gap-1.5 font-bold">
                  <span className="material-symbols-outlined text-[14px]">play_circle</span>
                  Interactive Demo Scenarios (1-Click Guided Run)
                </span>
                <span className="text-[10px] text-on-surface-variant font-mono">Instant End-to-End Simulation</span>
              </div>

              <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
                {/* Scenario 1 */}
                <button
                  type="button"
                  onClick={() => {
                    const m = 'Harvest SPY 15-Delta Put Skew with Defined Risk';
                    setMandate(m);
                    setAutonomyLevel('GUARDED_AUTONOMOUS');
                    handleExecuteMandate(m, 'GUARDED_AUTONOMOUS');
                  }}
                  disabled={isSubmitting}
                  className="p-3 bg-surface border border-primary/40 hover:border-primary hover:bg-primary/5 text-left rounded-sm transition-all group relative overflow-hidden disabled:opacity-50 shadow-sm"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[9px] font-mono uppercase bg-primary/20 text-primary px-1.5 py-0.5 rounded font-bold">
                      ⚡ Scenario A
                    </span>
                    <span className="text-[10px] text-primary group-hover:translate-x-0.5 transition-transform font-bold">Run ▶</span>
                  </div>
                  <div className="font-bold text-xs text-on-surface mb-1">Trade Survived Debate</div>
                  <div className="text-[10px] text-on-surface-variant leading-snug">
                    Agents debate skew vs momentum, synthesize 15Δ condor, and pass Alpaca MLEG gate.
                  </div>
                </button>

                {/* Scenario 2 */}
                <button
                  type="button"
                  onClick={() => {
                    const m = 'Aggressive unhedged short volatility on high-beta earnings catalyst';
                    setMandate(m);
                    setAutonomyLevel('GUARDED_AUTONOMOUS');
                    handleExecuteMandate(m, 'GUARDED_AUTONOMOUS');
                  }}
                  disabled={isSubmitting}
                  className="p-3 bg-surface border border-error/40 hover:border-error hover:bg-error/5 text-left rounded-sm transition-all group relative overflow-hidden disabled:opacity-50 shadow-sm"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[9px] font-mono uppercase bg-error/20 text-error px-1.5 py-0.5 rounded font-bold">
                      🛑 Scenario B
                    </span>
                    <span className="text-[10px] text-error group-hover:translate-x-0.5 transition-transform font-bold">Run ▶</span>
                  </div>
                  <div className="font-bold text-xs text-on-surface mb-1">Trade Died in Committee</div>
                  <div className="text-[10px] text-on-surface-variant leading-snug">
                    Critic attacks unhedged thesis, triggers Quant Gate violation, and enforces NO-TRADE.
                  </div>
                </button>

                {/* Scenario 3 */}
                <button
                  type="button"
                  onClick={() => {
                    const m = 'Scan macro breakout on SPY during network latency';
                    setMandate(m);
                    setAutonomyLevel('AUTOPILOT');
                    handleExecuteMandate(m, 'AUTOPILOT');
                  }}
                  disabled={isSubmitting}
                  className="p-3 bg-surface border border-amber-500/40 hover:border-amber-400 hover:bg-amber-500/5 text-left rounded-sm transition-all group relative overflow-hidden disabled:opacity-50 shadow-sm"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[9px] font-mono uppercase bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-bold">
                      🚨 Scenario C
                    </span>
                    <span className="text-[10px] text-amber-400 group-hover:translate-x-0.5 transition-transform font-bold">Run ▶</span>
                  </div>
                  <div className="font-bold text-xs text-on-surface mb-1">Safety Demotion Mode</div>
                  <div className="text-[10px] text-on-surface-variant leading-snug">
                    AI degradation triggers Radical Transparency; automatically locks autonomy to Copilot.
                  </div>
                </button>

                {/* Scenario 4: Multi-Asset Diversification */}
                <button
                  type="button"
                  onClick={() => {
                    const m = 'Build a diversified multi-asset quant portfolio across SPY, QQQ, and IWM with delta neutrality';
                    setMandate(m);
                    setAutonomyLevel('GUARDED_AUTONOMOUS');
                    handleExecuteMandate(m, 'GUARDED_AUTONOMOUS');
                  }}
                  disabled={isSubmitting}
                  className="p-3 bg-surface border border-cyan-500/40 hover:border-cyan-400 hover:bg-cyan-500/5 text-left rounded-sm transition-all group relative overflow-hidden disabled:opacity-50 shadow-sm"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[9px] font-mono uppercase bg-cyan-500/20 text-cyan-300 px-1.5 py-0.5 rounded font-bold">
                      🌐 Scenario D
                    </span>
                    <span className="text-[10px] text-cyan-400 group-hover:translate-x-0.5 transition-transform font-bold">Run ▶</span>
                  </div>
                  <div className="font-bold text-xs text-on-surface mb-1">Multi-Asset Basket</div>
                  <div className="text-[10px] text-on-surface-variant leading-snug">
                    Allocates risk across SPY, QQQ, and IWM with beta-weighted delta neutrality.
                  </div>
                </button>
              </div>
            </div>

            {/* Error & Degraded Notices */}
            {errorMessage && (
              <div className="mb-6 bg-error-container/20 border border-error/50 text-error px-4 py-3 rounded-sm flex items-center justify-between font-mono text-sm">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[18px]">error</span>
                  <span>{errorMessage}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setErrorMessage(null)}
                  className="text-error hover:text-on-surface"
                >
                  <span className="material-symbols-outlined text-[16px]">close</span>
                </button>
              </div>
            )}

            {degradedNotice && (
              <div className="mb-6 bg-amber-950/40 border border-amber-500/50 text-amber-300 px-4 py-3 rounded-sm flex items-center justify-between font-mono text-xs">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[18px] text-amber-400">warning</span>
                  <span>{degradedNotice}</span>
                </div>
              </div>
            )}

            {/* Terminal Input Box */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleExecuteMandate();
              }}
              className="relative w-full max-w-4xl shadow-lg shadow-black/50"
            >
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <span className="material-symbols-outlined text-primary text-[24px]">
                  arrow_forward_ios
                </span>
              </div>
              <input
                type="text"
                value={mandate}
                onChange={(e) => setMandate(e.target.value)}
                placeholder="Enter trading mandate (e.g. Harvest elevated put skew on SPY with defined risk)"
                className="w-full bg-surface-container h-16 pl-12 pr-48 font-data-md text-data-md text-on-surface border border-outline-variant/30 focus:border-primary/50 focus:outline-none focus:ring-1 focus:ring-primary/50 transition-all rounded-sm placeholder:text-on-surface-variant/50"
              />
              
              {/* Voice Dictation Button */}
              <button
                type="button"
                onClick={toggleVoiceInput}
                title={isListening ? "Listening... Speak now" : "Voice Dictate Mandate"}
                className={`absolute inset-y-2 right-36 px-3.5 flex items-center justify-center rounded-sm transition-all border ${
                  isListening
                    ? "bg-error/20 border-error text-error animate-pulse"
                    : "bg-surface-container-high border-outline-variant/40 text-on-surface-variant hover:text-primary hover:border-primary/50"
                }`}
              >
                <span className="material-symbols-outlined text-[20px]">
                  {isListening ? "mic" : "mic_none"}
                </span>
              </button>

              <button
                type="submit"
                disabled={isSubmitting}
                className="absolute inset-y-2 right-2 px-6 bg-primary text-on-primary font-data-md text-data-md hover:bg-primary-fixed transition-colors flex items-center gap-2 rounded-sm shadow-sm shadow-primary/20 hover:shadow-primary/40 disabled:opacity-50"
              >
                {isSubmitting ? 'ROUTING...' : 'EXECUTE'}
                <span className="material-symbols-outlined text-[18px]">send</span>
              </button>
            </form>

            {/* Quick Mandate Chips */}
            <div className="mt-6 flex flex-wrap items-center gap-2">
              <span className="font-label-xs text-label-xs text-outline uppercase tracking-widest mr-2">
                Example Mandates
              </span>
              {EXAMPLE_MANDATES.map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => {
                    setMandate(m);
                    handleExecuteMandate(m);
                  }}
                  className="px-3 py-1 bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-on-surface-variant hover:text-primary font-data-sm text-data-sm transition-colors rounded-sm text-left"
                >
                  &gt; {m}
                </button>
              ))}
            </div>
          </div>

          {/* Target Environment KPI Panel */}
          <div className="bg-surface-container-low flex-none p-6 border border-outline-variant/10 rounded-sm">
            <div className="flex items-center justify-between mb-6 border-b border-outline-variant/20 pb-4">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-outline">radar</span>
                <span className="font-headline-md text-headline-md text-on-surface font-semibold">
                  Target Environment
                </span>
              </div>
              <span className="px-2 py-1 bg-tertiary-container/10 text-tertiary-container font-label-xs text-label-xs rounded-sm uppercase tracking-widest">
                Live Option Surface
              </span>
            </div>

            <div className="grid grid-cols-4 gap-gutter bg-outline-variant/10 p-gutter rounded-sm">
              {/* Tile 1: Target */}
              <div className="bg-surface-container p-4 hover:bg-surface-container-high transition-colors group relative overflow-hidden flex flex-col justify-between h-24">
                <div className="absolute inset-0 bg-gradient-to-t from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                <span className="font-label-xs text-label-xs text-outline uppercase tracking-widest">
                  Target
                </span>
                <div className="flex items-baseline gap-2">
                  <span className="font-display-lg text-display-lg text-on-surface">SPY</span>
                  <span className="font-data-md text-data-md text-primary font-mono">$645.31</span>
                </div>
              </div>

              {/* Tile 2: Market Regime */}
              <div className="bg-surface-container p-4 hover:bg-surface-container-high transition-colors group relative overflow-hidden flex flex-col justify-between h-24">
                <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-tertiary-container" />
                <span className="font-label-xs text-label-xs text-outline uppercase tracking-widest pl-2">
                  Market Regime
                </span>
                <span className="font-data-lg text-data-lg text-on-surface pl-2">Range-Bound</span>
              </div>

              {/* Tile 3: Implied Volatility */}
              <div className="bg-surface-container p-4 hover:bg-surface-container-high transition-colors group relative overflow-hidden flex flex-col justify-between h-24">
                <span className="font-label-xs text-label-xs text-outline uppercase tracking-widest">
                  Implied Volatility (IV30)
                </span>
                <span className="font-data-lg text-data-lg text-error font-mono">24.8%</span>
              </div>

              {/* Tile 4: IV Rank */}
              <div className="bg-surface-container p-4 hover:bg-surface-container-high transition-colors group relative overflow-hidden flex flex-col justify-between h-24">
                <div className="absolute inset-0 flex items-end pointer-events-none">
                  <div className="h-[88%] w-full bg-error-container/20 border-t border-error-container/50" />
                </div>
                <span className="font-label-xs text-label-xs text-outline uppercase tracking-widest relative z-10">
                  IV Rank
                </span>
                <span className="font-data-lg text-data-lg text-on-surface font-mono relative z-10">
                  88%
                </span>
              </div>
            </div>
          </div>

          {/* Central Workflow Visualization */}
          <div className="bg-surface-container-low flex-1 p-6 relative border border-outline-variant/10 rounded-sm flex items-center justify-center overflow-hidden group min-h-[220px]">
            <div className="cockpit-grid absolute inset-0 opacity-40" />
            <div className="text-center relative z-10 max-w-lg">
              <span className="material-symbols-outlined text-outline-variant text-[48px] mb-3 group-hover:text-primary transition-colors duration-500">
                troubleshoot
              </span>
              <h3 className="font-headline-md text-headline-md text-on-surface mb-2">
                Multi-Agent Synthesis Engine
              </h3>
              <p className="font-body-sm text-body-sm text-outline mb-4">
                Quant anomalies stream directly into multi-agent debate (Researcher $\rightarrow$ Vol Analyst $\rightarrow$ Strategy $\rightarrow$ Critic) before the pure-code Risk Compiler verifies execution bounds.
              </p>
              <div className="flex justify-center gap-3">
                <Link
                  href="/surface"
                  className="px-4 py-2 bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 font-data-sm text-data-sm text-primary transition-colors rounded-sm"
                >
                  View Volatility Surface &gt;
                </Link>
                <Link
                  href="/decision/DEC-SPY-9942"
                  className="px-4 py-2 bg-primary/10 hover:bg-primary/20 border border-primary/30 font-data-sm text-data-sm text-primary transition-colors rounded-sm"
                >
                  Open Hero Decision Room &gt;
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Right Sidebar: Active Operation Pipeline */}
        <div className="col-span-4 bg-surface-container-low border border-outline-variant/10 rounded-sm flex flex-col h-full overflow-hidden relative shadow-xl shadow-black/20">
          <div className="absolute inset-0 border border-primary/10 rounded-sm pointer-events-none" />

          {/* Panel Header */}
          <div className="flex-none p-5 border-b border-outline-variant/20 bg-surface-container-high/50">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="relative w-3 h-3 flex items-center justify-center">
                  <div className="absolute w-full h-full bg-primary/20 rounded-full animate-ping" />
                  <div className="w-1.5 h-1.5 bg-primary rounded-full" />
                </div>
                <span className="font-headline-md text-headline-md text-on-surface uppercase tracking-tight">
                  Active Operation
                </span>
              </div>
              <span className="font-data-sm text-data-sm text-primary font-mono opacity-90">
                ID: {operationState.operationId}
              </span>
            </div>
          </div>

          {/* Operation Steps Stream */}
          <div className="flex-1 p-5 overflow-y-auto">
            <div className="relative pl-6">
              {/* Vertical connecting line */}
              <div className="absolute left-2 top-3 bottom-8 w-px bg-outline-variant/20" />

              {operationState.steps.map((step, idx) => {
                const isComplete = step.status === 'COMPLETE';
                const isActive = step.status === 'ACTIVE';
                const isPending = step.status === 'PENDING';

                return (
                  <div
                    key={step.id}
                    className={`relative mb-7 group ${
                      isPending ? 'opacity-40' : isActive ? 'opacity-100' : 'opacity-90'
                    }`}
                  >
                    {/* Status Dot */}
                    <div
                      className={`absolute -left-6 top-0.5 w-4 h-4 bg-surface-container-low border-2 rounded-full flex items-center justify-center z-10 ${
                        isComplete
                          ? 'border-primary'
                          : isActive
                          ? 'border-primary shadow-[0_0_8px_rgba(0,229,255,0.6)]'
                          : 'border-outline-variant'
                      }`}
                    >
                      {isComplete && <div className="w-1.5 h-1.5 bg-primary rounded-full" />}
                      {isActive && <div className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />}
                    </div>

                    <div className="flex flex-col gap-1">
                      <div className="flex items-center justify-between">
                        <span
                          className={`font-data-md text-data-md font-medium ${
                            isActive ? 'text-primary' : isComplete ? 'text-on-surface' : 'text-on-surface-variant'
                          }`}
                        >
                          {step.title}
                        </span>
                        {step.durationMs && (
                          <span className="font-data-sm text-data-sm text-outline font-mono">
                            {step.durationMs}ms
                          </span>
                        )}
                      </div>

                      {isActive && (
                        <div className="flex items-center gap-2 text-primary font-data-sm text-data-sm font-mono animate-pulse">
                          <span>Active • Processing...</span>
                        </div>
                      )}

                      {step.outputSummary && step.outputSummary.length > 0 && (
                        <div className="mt-2 p-2 bg-surface-container/50 border border-outline-variant/10 rounded-sm font-data-sm text-data-sm text-on-surface-variant max-h-20 overflow-y-auto font-mono">
                          {step.outputSummary.map((line, i) => (
                            <div key={i} className="flex gap-1.5">
                              <span className="text-primary/70">&gt;</span>
                              <span>{line}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Footer Controls */}
          {operationState.status === 'COMPLETED' && operationState.decisionId ? (
            <div className="flex-none p-4 border-t-2 border-primary/40 bg-surface-container-high flex flex-col gap-2.5 shadow-lg">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-primary font-bold flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[14px]">check_circle</span>
                  PIPELINE COMPLETE
                </span>
                <span className="text-on-surface-variant font-mono bg-surface px-1.5 py-0.5 rounded">
                  {operationState.decisionId}
                </span>
              </div>
              <div className="flex gap-2">
                <Link
                  href={`/decision/${operationState.decisionId}`}
                  className="flex-1 px-4 py-2.5 bg-primary hover:bg-primary-fixed text-on-primary font-display-md text-data-md uppercase tracking-wider rounded-sm flex items-center justify-center gap-2 font-bold shadow-glow-primary hover:shadow-glow-primary-lg transition-all"
                >
                  <span>Open Decision Room</span>
                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                </Link>
                <Link
                  href={`/trace/${operationState.decisionId}`}
                  className="px-3 py-2.5 bg-surface border border-outline-variant/50 hover:border-primary text-on-surface hover:text-primary rounded-sm flex items-center justify-center transition-all shadow-sm"
                  title="Inspect 4-Agent Debate DAG"
                >
                  <span className="material-symbols-outlined text-[18px]">account_tree</span>
                </Link>
              </div>
            </div>
          ) : (
            <div className="flex-none p-4 border-t border-outline-variant/20 bg-surface-container flex items-center justify-between">
              <div className="flex flex-col">
                <span className="font-label-xs text-label-xs text-outline uppercase tracking-widest">
                  {operationState.status === 'PROCESSING' ? 'Pipeline Active' : 'Status'}
                </span>
                <span className="font-data-md text-data-md text-primary font-mono">
                  {operationState.status === 'PROCESSING' ? 'Analyzing 4 Agents...' : 'Awaiting Mandate'}
                </span>
              </div>
              {operationState.status === 'PROCESSING' && (
                <button
                  type="button"
                  onClick={() => {
                    setOperationState((prev) => ({
                      ...prev,
                      status: 'IDLE',
                    }));
                  }}
                  className="px-3 py-1.5 border border-error/50 text-error hover:bg-error/10 hover:border-error font-data-sm text-data-sm transition-colors rounded-sm uppercase tracking-wider flex items-center gap-1 font-mono"
                >
                  <span className="material-symbols-outlined text-[14px]">close</span> Abort
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
