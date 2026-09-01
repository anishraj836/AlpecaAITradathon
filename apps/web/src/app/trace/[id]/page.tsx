'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { AgentTraceStep } from '@/types/voltron';

export default function AgentTracePage() {
  const params = useParams();
  const decisionId = typeof params?.id === 'string' ? params.id : '';

  const [traceSteps, setTraceSteps] = useState<AgentTraceStep[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({
    'step-1': true,
    'step-4': true,
    'step-5': true,
  });

  useEffect(() => {
    let isMounted = true;
    if (decisionId) {
      setIsLoading(true);
      api.getAgentTrace(decisionId).then((steps) => {
        if (isMounted) {
          setTraceSteps(steps);
          setIsLoading(false);
        }
      }).catch(() => {
        if (isMounted) setIsLoading(false);
      });
    }
    return () => {
      isMounted = false;
    };
  }, [decisionId]);

  const toggleNode = (id: string) => {
    setExpandedNodes((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="flex flex-col w-full text-on-surface h-full pb-container-gap">
      <div className="w-full flex-1 relative flex flex-col p-6 gap-6 max-w-[1200px] mx-auto overflow-hidden">
        {/* Header Section */}
        <div className="flex flex-col gap-2 mb-2 shrink-0 relative z-10">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-primary text-[28px]">
              account_tree
            </span>
            <h1 className="font-display-lg text-display-lg text-on-surface font-bold">
              Agent Trace Pipeline
            </h1>
          </div>
          <div className="flex items-center gap-4 border-b border-outline-variant/30 pb-4">
            <p className="font-data-md text-data-md text-on-surface-variant max-w-2xl font-mono">
              Real-time execution reasoning timeline. Tracking multi-agent consensus for{' '}
              <span className="text-primary-fixed-dim font-bold">{decisionId}</span>.
            </p>
            <div className="ml-auto flex items-center gap-3 bg-surface-container-low px-3 py-1.5 rounded-sm border border-outline-variant/20 shadow-sm font-mono text-xs">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-fixed opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-primary-fixed-dim" />
              </span>
              <span className="font-label-xs text-label-xs tracking-widest uppercase text-on-surface-variant">
                Trace Verified
              </span>
            </div>
          </div>
        </div>

        {/* Timeline Container */}
        <div className="relative flex-1 flex flex-col gap-6 pb-8 w-full max-w-4xl mx-auto z-10">
          {/* Vertical Track */}
          <div className="absolute left-[39px] top-4 bottom-0 w-[2px] bg-outline-variant/30 z-0" />

          {traceSteps.map((step) => {
            const isExpanded = !!expandedNodes[step.id];
            const isRiskCompiler = step.agentRole === 'RISK_COMPILER';
            const isCritic = step.agentRole === 'CRITIC';
            const isResearcher = step.agentRole === 'RESEARCHER';
            const isVolAnalyst = step.agentRole === 'VOLATILITY_ANALYST';

            return (
              <div
                key={step.id}
                onClick={() => toggleNode(step.id)}
                className="relative z-10 flex gap-6 group cursor-pointer"
              >
                {/* Agent Icon Badge */}
                <div className="relative flex-shrink-0 w-20 flex justify-center mt-1">
                  <div
                    className={`w-8 h-8 rounded-full bg-surface-container-high border-2 flex items-center justify-center transition-all group-hover:scale-110 ${
                      isRiskCompiler
                        ? 'border-primary shadow-glow-primary'
                        : isCritic
                        ? 'border-error shadow-glow-error'
                        : isVolAnalyst
                        ? 'border-secondary shadow-glow-secondary'
                        : isResearcher
                        ? 'border-primary-fixed-dim shadow-glow-primary'
                        : 'border-tertiary-fixed-dim shadow-glow-tertiary'
                    }`}
                  >
                    <span
                      className={`material-symbols-outlined text-[16px] ${
                        isRiskCompiler
                          ? 'text-primary'
                          : isCritic
                          ? 'text-error'
                          : isVolAnalyst
                          ? 'text-secondary-fixed-dim'
                          : isResearcher
                          ? 'text-primary-fixed-dim'
                          : 'text-tertiary-fixed-dim'
                      }`}
                    >
                      {isRiskCompiler
                        ? 'done_all'
                        : isCritic
                        ? 'gavel'
                        : isVolAnalyst
                        ? 'query_stats'
                        : isResearcher
                        ? 'travel_explore'
                        : 'architecture'}
                    </span>
                  </div>
                </div>

                {/* Step Content Card */}
                <div
                  className={`flex-1 bg-surface-container rounded-sm p-5 border shadow-md transition-all group-hover:bg-surface-container-high relative overflow-hidden ${
                    isRiskCompiler
                      ? 'border-primary/40'
                      : isCritic
                      ? 'border-error/40'
                      : 'border-outline-variant/20'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2 font-mono">
                    <div className="flex items-center gap-2">
                      <span
                        className={`font-label-xs text-label-xs uppercase tracking-widest ${
                          isRiskCompiler
                            ? 'text-primary'
                            : isCritic
                            ? 'text-error'
                            : isVolAnalyst
                            ? 'text-secondary-fixed-dim'
                            : 'text-primary-fixed-dim'
                        }`}
                      >
                        {step.agentLabel}
                      </span>
                      <span className="font-data-md text-data-md text-on-surface bg-surface-variant px-2 py-0.5 rounded-sm font-bold">
                        {step.agentRole.replace('_', ' ')}
                      </span>
                      {isRiskCompiler ? (
                        <span className="text-[10px] text-primary bg-primary/10 border border-primary/20 px-1.5 py-0.5 rounded-sm">
                          PURE CODE (DETERMINISTIC)
                        </span>
                      ) : step.executionMode === 'HEURISTIC_FALLBACK' ? (
                        <span className="text-[10px] text-amber-400 bg-amber-500/10 border border-amber-500/30 px-1.5 py-0.5 rounded-sm font-mono font-bold">
                          FALLBACK HEURISTIC (NO LLM)
                        </span>
                      ) : (
                        <span className="text-[10px] text-cyan-400 bg-cyan-500/10 border border-cyan-500/30 px-1.5 py-0.5 rounded-sm font-mono">
                          LLM: {(step.providerName || 'GEMINI').toUpperCase()}
                        </span>
                      )}
                    </div>
                    <span className="font-data-sm text-data-sm text-on-surface-variant">
                      {step.timestampOffset}
                    </span>
                  </div>

                  <h3 className="font-headline-md text-headline-md text-on-surface mb-2 font-semibold">
                    {step.title}
                  </h3>

                  {step.tags && step.tags.length > 0 && (
                    <div className="flex gap-2 mb-3">
                      {step.tags.map((t, i) => (
                        <span
                          key={i}
                          className={`inline-flex items-center gap-1 font-label-xs text-label-xs px-2 py-1 rounded-sm border font-mono ${
                            t.variant === 'primary'
                              ? 'bg-primary text-background font-bold border-primary'
                              : t.variant === 'error'
                              ? 'bg-error-container/20 text-error border-error-container/30 font-bold'
                              : t.variant === 'secondary'
                              ? 'bg-secondary-container/20 text-secondary-fixed border-secondary-container/30'
                              : 'bg-tertiary-container/20 text-tertiary-fixed border-tertiary-container/30'
                          }`}
                        >
                          {t.label}
                        </span>
                      ))}
                    </div>
                  )}

                  <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
                    {step.summary}
                  </p>

                  {/* Expandable Details Drawer */}
                  {isExpanded && step.details && (
                    <div className="mt-4 pt-4 border-t border-outline-variant/20 font-mono text-xs">
                      {step.details.keyDrivers && (
                        <div>
                          <span className="block font-label-xs text-label-xs text-outline mb-1 uppercase font-sans">
                            Key Drivers
                          </span>
                          <ul className="space-y-1 text-on-surface-variant list-none pl-0">
                            {step.details.keyDrivers.map((driver, idx) => (
                              <li key={idx} className="flex items-center gap-2">
                                <span className="w-1 h-1 bg-primary rounded-full" />
                                <span>{driver}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {step.details.metrics && (
                        <div className="grid grid-cols-3 gap-2">
                          <div className="text-outline uppercase text-[10px]">Metric</div>
                          <div className="text-outline uppercase text-[10px]">Current</div>
                          <div className="text-outline uppercase text-[10px]">Baseline</div>
                          {step.details.metrics.map((m, i) => (
                            <React.Fragment key={i}>
                              <span className="text-on-surface">{m.label}</span>
                              <span className="text-primary font-bold">{m.current}</span>
                              <span className="text-on-surface-variant">{m.baseline}</span>
                            </React.Fragment>
                          ))}
                        </div>
                      )}

                      {step.details.recommendations && (
                        <div className="p-2 bg-surface-container-low border border-outline-variant/20 rounded-sm">
                          <span className="font-label-xs text-label-xs text-outline uppercase font-sans">
                            Critic Recommendation
                          </span>
                          <div className="text-primary-fixed-dim mt-1">
                            {step.details.recommendations[0]}
                          </div>
                        </div>
                      )}

                      {step.details.riskMetrics && (
                        <div className="grid grid-cols-4 gap-3 bg-surface p-3 rounded-sm border border-primary/20">
                          {step.details.riskMetrics.map((rm, i) => (
                            <div key={i} className="flex flex-col">
                              <span className="text-outline uppercase text-[10px]">{rm.label}</span>
                              <span className="text-primary font-bold text-sm">{rm.value}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="mt-3 flex justify-end">
                    <span className="material-symbols-outlined text-outline-variant group-hover:text-primary transition-colors text-[20px]">
                      {isExpanded ? 'expand_less' : 'expand_more'}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer Navigation */}
        <div className="flex justify-between items-center pt-4 border-t border-outline-variant/20">
          <Link
            href={`/decision/${decisionId}`}
            className="px-4 py-2 bg-primary text-on-primary font-data-md text-data-md rounded-sm font-bold uppercase tracking-wider hover:bg-primary-fixed transition-colors"
          >
            &lt; Return to Decision Room
          </Link>
        </div>
      </div>
    </div>
  );
}
