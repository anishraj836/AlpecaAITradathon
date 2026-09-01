'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { DecisionPacket, OrderResult } from '@/types/voltron';

export default function DecisionRoomPage() {
  const params = useParams();
  const decisionId = typeof params?.id === 'string' ? params.id : '';

  const [decision, setDecision] = useState<DecisionPacket | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [orderResult, setOrderResult] = useState<OrderResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [activeLegIndex, setActiveLegIndex] = useState<number | null>(null);

  useEffect(() => {
    let isMounted = true;
    if (decisionId) {
      setIsLoading(true);
      api.getDecision(decisionId).then(async (data) => {
        if (isMounted) {
          setDecision(data);
          setIsLoading(false);
          if (data.status === 'APPROVED' || data.status === 'EXECUTED') {
            try {
              const ord = await api.getOrder(decisionId);
              if (isMounted) setOrderResult(ord);
            } catch (e) {
              console.warn('Could not load order details:', e);
            }
          }
        }
      }).catch((err) => {
        if (isMounted) {
          setIsLoading(false);
          setErrorMessage(`Decision '${decisionId}' was not found in database.`);
        }
      });
    }
    return () => {
      isMounted = false;
    };
  }, [decisionId]);

  const handleConfirmApproval = async () => {
    setShowConfirmModal(false);
    if (isProcessing || !decision || decision.status === 'APPROVED' || decision.status === 'EXECUTED') return;
    setIsProcessing(true);
    setErrorMessage(null);

    try {
      const result = await api.approveDecision(decision.id);
      setOrderResult(result);
      setDecision((prev) => (prev ? { ...prev, status: 'APPROVED' } : prev));
    } catch (err: any) {
      console.error('Approval failed:', err);
      setErrorMessage(err?.message || 'Failed to approve and route order.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRejectOrder = async () => {
    if (isProcessing || !decision) return;
    setIsProcessing(true);
    setErrorMessage(null);

    try {
      await api.rejectDecision(decision.id);
      setDecision((prev) => (prev ? { ...prev, status: 'REJECTED' } : prev));
    } catch (err: any) {
      console.error('Rejection failed:', err);
      setErrorMessage(err?.message || 'Failed to reject decision.');
    } finally {
      setIsProcessing(false);
    }
  };

  if (!decision) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh] gap-3">
        {isLoading ? (
          <>
            <span className="material-symbols-outlined text-[42px] text-primary animate-spin">refresh</span>
            <p className="font-mono text-sm text-on-surface font-bold">Loading Decision Packet from Database...</p>
          </>
        ) : (
          <div className="bg-surface-container p-6 border border-error/40 rounded-sm text-center max-w-md">
            <span className="material-symbols-outlined text-error text-[36px] mb-2">error</span>
            <p className="font-mono text-sm text-on-surface font-bold">{errorMessage || `Decision '${decisionId}' was not found in database.`}</p>
            <Link href="/terminal" className="mt-4 inline-block px-4 py-1.5 bg-primary text-on-primary font-mono text-xs rounded-sm font-bold">
              Return to Terminal
            </Link>
          </div>
        )}
      </div>
    );
  }

  const strategy = decision.strategy;

  return (
    <div className="flex flex-col w-full h-full gap-container-gap pb-container-gap relative">
      {/* Top Header Strip */}
      <div className="bg-surface-container border-l-2 border-primary p-4 flex justify-between items-center relative overflow-hidden group hover:bg-surface-container-high transition-colors">
        <div className="absolute inset-0 bg-gradient-to-r from-primary/5 to-transparent pointer-events-none" />
        <div className="flex items-baseline gap-4 relative z-10">
          <h1 className="font-display-lg text-display-lg text-on-surface uppercase tracking-tight font-bold">
            VOLTRON DECISION ROOM
          </h1>
          <div className="w-px h-6 bg-outline-variant/30" />
          <span className="font-data-lg text-data-lg text-primary-fixed-dim font-mono font-bold">
            {decision.underlying}
          </span>
          <div className="w-px h-6 bg-outline-variant/30" />
          <span className="font-data-lg text-data-lg text-tertiary-fixed-dim font-mono">
            {strategy.name.toUpperCase()}
          </span>
          <div className="w-px h-6 bg-outline-variant/30" />
          <span className="font-data-sm text-data-sm text-outline font-mono">
            {decision.id}
          </span>
        </div>

        {/* AI Confidence Meter & Autonomy Governance */}
        <div className="flex items-center gap-3 relative z-10">
          <div className={`px-3 py-1.5 rounded text-xs font-mono border flex items-center gap-1.5 ${
            decision.autonomyLevel === 'COPILOT'
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
              : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300'
          }`}>
            <span className="font-bold">{decision.autonomyLevel || 'GUARDED_AUTONOMOUS'}</span>
          </div>

          <div className="flex items-center gap-3 bg-surface px-4 py-2 ring-1 ring-outline-variant/30 rounded-sm">
            <span className="font-label-xs text-label-xs text-outline uppercase tracking-widest">
              Lognormal POP
            </span>
            <span className="font-data-lg text-data-lg font-mono font-bold text-primary">
              {(strategy.pop * 100).toFixed(1)}%
            </span>
            <div className="w-16 h-1.5 bg-surface-variant ml-2 overflow-hidden rounded-full">
              <div
                className="h-full bg-primary"
                style={{ width: `${Math.min(100, Math.round(strategy.pop * 100))}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Degraded Mode Radical Transparency Banner */}
      {decision.isDegradedMode && (
        <div className="bg-amber-950/40 border border-amber-500/50 text-amber-300 px-4 py-3 rounded-sm flex items-center justify-between font-mono text-xs shadow-lg">
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-[20px] text-amber-400">gavel</span>
            <div>
              <span className="font-bold">RADICAL TRANSPARENCY NOTICE: </span>
              <span>
                LLM committee was offline. This trade was synthesized via deterministic quantitative rules. Autonomous execution was safely locked.
              </span>
            </div>
          </div>
          <span className="px-2 py-0.5 bg-amber-500/20 text-amber-300 rounded text-[10px] border border-amber-500/40 uppercase">
            Human Approval Mandatory
          </span>
        </div>
      )}

      {/* Error Alert Banner */}
      {errorMessage && (
        <div className="bg-error-container/20 border border-error/50 text-error px-4 py-3 rounded-sm flex items-center justify-between font-mono text-sm">
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

      {/* Main 12-Column Grid */}
      <div className="flex-1 grid grid-cols-12 gap-container-gap min-h-0">
        {/* Left Column (span 3): Market Context & Volatility Evidence */}
        <div className="col-span-3 flex flex-col gap-container-gap">
          <div className="flex-1 bg-surface-container p-4 flex flex-col relative rounded-sm border border-outline-variant/20">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-outline-variant text-[16px]">
                subject
              </span>
              <h2 className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-widest">
                Market Context
              </h2>
            </div>

            <div className="space-y-4 mb-6">
              <div className="flex justify-between items-baseline border-b border-outline-variant/20 pb-2">
                <span className="font-body-sm text-body-sm text-on-surface-variant">Underlying Price</span>
                <span className="font-data-md text-data-md text-on-surface font-mono font-bold">
                  ${decision.spotPrice.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between items-baseline border-b border-outline-variant/20 pb-2">
                <span className="font-body-sm text-body-sm text-on-surface-variant">Implied Vol (IV30)</span>
                <span className="font-data-md text-data-md text-tertiary-fixed-dim font-mono">
                  {decision.iv30.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-baseline border-b border-outline-variant/20 pb-2">
                <span className="font-body-sm text-body-sm text-on-surface-variant">IV Rank</span>
                <span className="font-data-md text-data-md text-primary-fixed-dim font-mono">
                  {decision.ivRank.toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between items-baseline border-b border-outline-variant/20 pb-2">
                <span className="font-body-sm text-body-sm text-on-surface-variant">Regime</span>
                <span className="font-data-sm text-data-sm text-on-surface font-mono bg-surface px-1.5 py-0.5 rounded-sm">
                  {decision.marketRegime}
                </span>
              </div>
            </div>

            {/* Volatility Evidence */}
            <div className="flex items-center gap-2 mb-2 mt-auto">
              <span className="material-symbols-outlined text-outline-variant text-[16px]">
                troubleshoot
              </span>
              <h2 className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-widest">
                Volatility Evidence
              </h2>
            </div>
            <div className="bg-surface p-3 ring-1 ring-outline-variant/20 h-28 relative flex items-center justify-center overflow-hidden group rounded-sm">
              <svg
                className="absolute inset-0 w-full h-full stroke-primary/40 group-hover:stroke-primary transition-all duration-500"
                viewBox="0 0 100 100"
                preserveAspectRatio="none"
              >
                <path d="M0,50 Q25,80 50,50 T100,50" fill="none" strokeWidth="2" />
                <path d="M0,40 Q25,20 50,60 T100,40" fill="none" stroke="#fec931" strokeWidth="1" strokeOpacity="0.4" />
              </svg>
              <div className="absolute bottom-2 left-2 right-2 flex justify-between font-mono">
                <span className="font-data-sm text-[10px] text-outline">Puts Bid (Rich)</span>
                <span className="font-data-sm text-[10px] text-outline">Calls Ask (Normal)</span>
              </div>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant mt-3 leading-relaxed">
              {decision.evidence.description}
            </p>
          </div>
        </div>

        {/* Center Column (span 6): Strategy Structure & Multi-Leg Architecture */}
        <div className="col-span-6 bg-surface-container flex flex-col p-6 relative group overflow-hidden rounded-sm border border-outline-variant/20">
          <div className="cockpit-grid absolute inset-0 opacity-15 pointer-events-none" />

          <div className="flex justify-between items-center mb-6 relative z-10">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-primary text-[24px]">architecture</span>
              <h2 className="font-headline-md text-headline-md text-on-surface tracking-tight font-semibold">
                Strategy Structure
              </h2>
            </div>
            <div className="bg-surface-variant px-3 py-1 ring-1 ring-outline-variant/30 flex items-center gap-2 rounded-sm">
              <div className="w-1.5 h-1.5 bg-tertiary-fixed-dim rounded-full" />
              <span className="font-data-sm text-data-sm text-on-surface uppercase font-mono">
                {strategy.legs.length} Legs / {strategy.dte} DTE
              </span>
            </div>
          </div>

          {/* Interactive Strike & Leg Visualizer */}
          <div className="flex-1 relative flex items-center justify-center my-4">
            <div className="absolute w-full h-px bg-outline-variant top-1/2 -translate-y-1/2 z-0" />
            <div className="absolute left-1/2 top-1/2 w-px h-28 bg-primary/30 -translate-x-1/2 -translate-y-1/2 z-0" />

            {/* Current Spot Price Pin */}
            <div className="absolute left-1/2 top-[28%] -translate-x-1/2 -translate-y-full flex flex-col items-center z-20">
              <span className="font-label-xs text-label-xs text-primary bg-surface px-2.5 py-1 rounded ring-1 ring-primary/40 shadow-md font-mono">
                CURRENT: ${decision.spotPrice.toFixed(2)}
              </span>
              <div className="w-px h-6 bg-primary/60 mt-1" />
              <div className="w-2 h-2 bg-primary rotate-45 -mt-1" />
            </div>

            {/* Legs Grid */}
            <div className="w-full flex justify-between relative z-10 px-4">
              {strategy.legs.map((leg, idx) => {
                const isBuy = leg.side === 'BUY';
                const isSelected = activeLegIndex === idx;

                return (
                  <div
                    key={leg.id}
                    onClick={() => setActiveLegIndex(isSelected ? null : idx)}
                    className="flex flex-col items-center group/leg cursor-pointer"
                  >
                    <div
                      className={`bg-surface p-2.5 ring-1 transition-all relative rounded-sm ${
                        isSelected
                          ? 'ring-primary shadow-glow-primary'
                          : isBuy
                          ? 'ring-outline-variant/50 hover:ring-tertiary-fixed-dim'
                          : 'ring-primary/50 hover:ring-primary shadow-[0_0_12px_rgba(0,229,255,0.15)]'
                      }`}
                    >
                      <span
                        className={`font-data-md text-data-md block text-center font-bold ${
                          isBuy ? 'text-on-surface' : 'text-primary'
                        }`}
                      >
                        {leg.side}
                      </span>
                      <span
                        className={`font-label-xs text-label-xs block text-center font-mono ${
                          isBuy ? 'text-outline' : 'text-primary-fixed-dim'
                        }`}
                      >
                        {leg.strike}
                        {leg.type === 'CALL' ? 'C' : 'P'}
                      </span>
                      <div
                        className={`absolute -top-1 -right-1 w-2 h-2 rounded-none ${
                          isBuy ? 'bg-error' : 'bg-tertiary-fixed-dim'
                        }`}
                      />
                    </div>
                    <div
                      className={`w-px h-6 my-2 ${
                        isBuy ? 'bg-outline-variant/50' : 'bg-primary/40'
                      }`}
                    />
                    <span
                      className={`font-data-sm text-data-sm font-mono ${
                        isBuy ? 'text-on-surface-variant' : 'text-primary font-bold'
                      }`}
                    >
                      {isBuy ? `-$${leg.mid.toFixed(2)}` : `+$${leg.mid.toFixed(2)}`}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Mini Payoff Profile Graphic */}
          <div className="w-full h-20 relative bg-surface/50 border border-outline-variant/20 rounded-sm overflow-hidden flex items-center justify-center mt-auto">
            <svg className="w-full h-full opacity-60" viewBox="0 0 400 80" preserveAspectRatio="none">
              <line x1="0" y1="40" x2="400" y2="40" stroke="#3b494c" strokeDasharray="4 4" />
              <path
                d="M0,65 L80,65 L150,15 L250,15 L320,65 L400,65"
                fill="none"
                stroke="#00e5ff"
                strokeWidth="2"
              />
              <path
                d="M0,65 L80,65 L150,15 L250,15 L320,65 L400,65 L400,80 L0,80 Z"
                fill="rgba(0, 229, 255, 0.08)"
              />
            </svg>
            <span className="absolute bottom-1 right-2 text-[10px] font-mono text-outline">
              Net Credit: ${strategy.netCreditOrDebit.toFixed(2)}/contract
            </span>
          </div>
        </div>

        {/* Right Column (span 3): Key Financial Metrics */}
        <div className="col-span-3 bg-surface-container flex flex-col rounded-sm border border-outline-variant/20 overflow-hidden">
          <div className="p-4 border-b border-outline-variant/20 flex items-center gap-2 bg-surface/50">
            <span className="material-symbols-outlined text-outline-variant text-[16px]">
              bar_chart
            </span>
            <h2 className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-widest">
              Canonical Metrics (Quant MCP)
            </h2>
          </div>

          <div className="flex-1 flex flex-col p-4 gap-3 justify-between">
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col bg-surface p-3 ring-1 ring-outline-variant/20 border-l-2 border-primary rounded-sm">
                <span className="font-label-xs text-label-xs text-outline uppercase mb-1">Max Profit</span>
                <span className="font-data-lg text-data-lg text-primary font-mono font-bold">
                  ${strategy.maxProfit.toFixed(2)}
                </span>
                <span className="font-data-sm text-[10px] text-on-surface-variant mt-1 font-mono">
                  Credit Received
                </span>
              </div>
              <div className="flex flex-col bg-surface p-3 ring-1 ring-outline-variant/20 border-l-2 border-error rounded-sm">
                <span className="font-label-xs text-label-xs text-outline uppercase mb-1">Max Loss</span>
                <span className="font-data-lg text-data-lg text-error font-mono font-bold">
                  -${strategy.maxLoss.toFixed(2)}
                </span>
                <span className="font-data-sm text-[10px] text-on-surface-variant mt-1 font-mono">
                  BP Allocation
                </span>
              </div>
            </div>

            {/* Probability of Profit POP */}
            <div className="flex flex-col bg-surface p-3 ring-1 ring-outline-variant/20 rounded-sm">
              <div className="flex justify-between items-center mb-1.5">
                <span className="font-label-xs text-label-xs text-outline uppercase">
                  Prob. of Profit (POP)
                </span>
                <span className="font-data-md text-data-md text-tertiary-fixed-dim font-mono font-bold">
                  {(strategy.pop * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full h-1.5 bg-surface-variant overflow-hidden rounded-full">
                <div
                  className="h-full bg-tertiary-fixed-dim"
                  style={{ width: `${strategy.pop * 100}%` }}
                />
              </div>
            </div>

            {/* Breakeven Corridor */}
            <div className="flex flex-col bg-surface p-3 ring-1 ring-outline-variant/20 rounded-sm">
              <span className="font-label-xs text-label-xs text-outline uppercase mb-1">
                Breakevens
              </span>
              <div className="flex justify-between font-mono">
                <span className="font-data-md text-data-md text-on-surface font-bold">
                  ${strategy.breakevens[0]?.toFixed(2)}
                </span>
                {strategy.breakevens.length > 1 && (
                  <>
                    <span className="font-data-sm text-data-sm text-outline-variant">--</span>
                    <span className="font-data-md text-data-md text-on-surface font-bold">
                      ${strategy.breakevens[1]?.toFixed(2)}
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Liquidity Score */}
            <div className="flex justify-between items-center bg-surface p-3 ring-1 ring-outline-variant/20 rounded-sm">
              <span className="font-label-xs text-label-xs text-outline uppercase">Liquidity Score</span>
              <div className="flex items-center gap-2">
                <span className="font-data-md text-data-md text-primary-fixed-dim font-mono font-bold">
                  {strategy.liquidityScore} / 100
                </span>
                <div className="w-2 h-2 rounded-full bg-primary-fixed-dim shadow-glow-primary" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Insights Row */}
      <div className="grid grid-cols-12 gap-container-gap min-h-48">
        {/* Why This Trade */}
        <div className="col-span-4 bg-surface-container p-4 flex flex-col border-t-2 border-outline-variant/30 rounded-sm">
          <h3 className="font-label-xs text-label-xs text-outline uppercase tracking-widest mb-3">
            Why This Trade?
          </h3>
          <ul className="space-y-2.5 flex-1 overflow-y-auto pr-1">
            {decision.whyThisTrade.map((point, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="material-symbols-outlined text-tertiary-fixed-dim text-[16px] mt-0.5">
                  check_circle
                </span>
                <span className="font-body-sm text-body-sm text-on-surface-variant leading-snug">
                  {point}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* AI Critic Analysis */}
        <div className="col-span-4 bg-surface-container p-4 flex flex-col border-t-2 border-error/50 relative overflow-hidden group rounded-sm">
          <div className="absolute top-0 right-0 p-2 opacity-10 pointer-events-none group-hover:opacity-20 transition-opacity">
            <span className="material-symbols-outlined text-[64px] text-error">warning</span>
          </div>
          <h3 className="font-label-xs text-label-xs text-error uppercase tracking-widest mb-2 flex items-center gap-1.5 font-bold">
            <span className="material-symbols-outlined text-[14px]">smart_toy</span>
            AI Critic Failure Mode Analysis
          </h3>
          <div className="flex-1 flex flex-col justify-center">
            <p className="font-data-sm text-data-sm text-on-surface bg-surface p-3 ring-1 ring-error/30 border-l-2 border-error leading-relaxed rounded-sm font-mono">
              <span className="text-error font-bold">PRIMARY FAILURE MODE:</span>{' '}
              {decision.criticAnalysis.primaryFailureMode} {decision.criticAnalysis.details}
            </p>
          </div>
        </div>

        {/* Deterministic Risk Compiler */}
        <div className="col-span-4 bg-surface-container p-4 flex flex-col border-t-2 border-primary/50 rounded-sm">
          <h3 className="font-label-xs text-label-xs text-primary uppercase tracking-widest mb-2 flex items-center gap-1.5 font-bold">
            <span className="material-symbols-outlined text-[14px]">terminal</span>
            Risk Compiler (Deterministic Pure Code)
          </h3>
          <div className="flex-1 flex flex-col justify-around font-mono">
            <div className="flex items-center justify-between text-xs">
              <span className="text-on-surface-variant font-sans">Budget Allocation</span>
              <span className="font-data-sm text-data-sm text-primary bg-primary/10 px-2 py-0.5 ring-1 ring-primary/30 rounded-sm font-bold">
                {decision.riskCompilerResult.budgetCheck.valueText}
              </span>
            </div>
            <div className="w-full h-px bg-outline-variant/20" />
            <div className="flex items-center justify-between text-xs">
              <span className="text-on-surface-variant font-sans">Liquidity Check</span>
              <span className="font-data-sm text-data-sm text-primary bg-primary/10 px-2 py-0.5 ring-1 ring-primary/30 rounded-sm font-bold">
                {decision.riskCompilerResult.liquidityCheck.valueText}
              </span>
            </div>
            <div className="w-full h-px bg-outline-variant/20" />
            <div className="flex items-center justify-between text-xs">
              <span className="text-on-surface-variant font-sans">Portfolio Concentration</span>
              <span className="font-data-sm text-data-sm text-tertiary-fixed-dim bg-tertiary-fixed-dim/10 px-2 py-0.5 ring-1 ring-tertiary-fixed-dim/30 rounded-sm font-bold">
                {decision.riskCompilerResult.concentrationCheck.valueText}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Action Execution Bar (Sticky to bottom of viewport) */}
      <div className="sticky bottom-2 left-0 right-0 z-40 bg-surface-container/95 backdrop-blur-md p-4 flex items-center justify-between border-2 border-outline-variant/40 rounded-sm shadow-[0_-8px_30px_rgba(0,0,0,0.6)] ring-1 ring-primary/20 mt-4">
        <div className="flex items-center gap-3.5">
          <div className="relative flex h-3.5 w-3.5">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                decision.status === 'APPROVED'
                  ? 'bg-primary'
                  : decision.status === 'REJECTED'
                  ? 'bg-error'
                  : 'bg-amber-400'
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-3.5 w-3.5 ${
                decision.status === 'APPROVED'
                  ? 'bg-primary'
                  : decision.status === 'REJECTED'
                  ? 'bg-error'
                  : 'bg-amber-400'
              }`}
            />
          </div>
          <div className="flex flex-col">
            <span className="font-data-md text-data-md text-on-surface uppercase tracking-wider font-mono font-bold">
              {decision.status === 'APPROVED'
                ? `ORDER ROUTED TO ALPACA (ORD ID: ${orderResult?.orderId || decision.id})`
                : decision.status === 'REJECTED'
                ? 'TRADE PROPOSAL REJECTED BY TRADER'
                : 'Waiting for Human Approval'}
            </span>
            <span className="text-[11px] text-on-surface-variant font-mono">
              {decision.status === 'APPROVED'
                ? 'Execution confirmed on Alpaca Paper Trading Gateway'
                : decision.status === 'REJECTED'
                ? 'Order execution blocked. Capital preserved.'
                : 'Human-in-the-Loop Governance: Review parameters before broker dispatch.'}
            </span>
          </div>
        </div>

        <div className="flex gap-4 items-center">
          {decision.status !== 'APPROVED' && decision.status !== 'REJECTED' && (
            <button
              type="button"
              onClick={handleRejectOrder}
              disabled={isProcessing}
              className="px-6 py-3 bg-surface border border-error/50 hover:bg-error/10 hover:border-error text-error font-data-md text-data-md uppercase tracking-wider transition-all rounded-sm disabled:opacity-40 flex items-center gap-2 font-bold shadow-sm cursor-pointer"
            >
              <span className="material-symbols-outlined text-[18px]">cancel</span>
              <span>Reject Trade</span>
            </button>
          )}

          {decision.status === 'APPROVED' ? (
            <Link
              href="/portfolio"
              className="px-8 py-3 bg-primary hover:bg-primary-fixed text-on-primary font-display-lg text-data-lg uppercase tracking-wider transition-all rounded-sm flex items-center gap-2 font-bold shadow-glow-primary hover:shadow-glow-primary-lg"
            >
              <span>View in Live Portfolio</span>
              <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
            </Link>
          ) : decision.status === 'REJECTED' ? (
            <Link
              href="/terminal"
              className="px-8 py-3 bg-surface border border-outline-variant hover:border-primary text-on-surface font-display-lg text-data-lg uppercase tracking-wider transition-all rounded-sm flex items-center gap-2 font-bold"
            >
              <span>Run New Scan in Terminal</span>
              <span className="material-symbols-outlined text-[20px]">refresh</span>
            </Link>
          ) : (
            <button
              type="button"
              onClick={() => setShowConfirmModal(true)}
              disabled={isProcessing}
              className="relative px-10 py-3 bg-primary hover:bg-primary-fixed text-on-primary font-display-lg text-data-lg uppercase tracking-wider transition-all overflow-hidden group shadow-glow-primary hover:shadow-glow-primary-lg rounded-sm disabled:opacity-40 flex items-center gap-2 font-bold cursor-pointer"
            >
              <span className="relative z-10 flex items-center gap-2 font-bold">
                {isProcessing ? 'Routing to Alpaca...' : 'Approve Paper Order'}
                <span className="material-symbols-outlined text-[20px] group-hover:translate-x-0.5 transition-transform">send</span>
              </span>
            </button>
          )}
        </div>
      </div>

      {/* Explicit Order Confirmation Modal (Human Approval Gate) */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-surface-container max-w-xl w-full border border-primary/50 shadow-2xl p-6 rounded-sm flex flex-col gap-5 animate-fade-in font-mono">
            <div className="flex items-center justify-between border-b border-outline-variant/30 pb-3">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-primary text-[24px]">verified_user</span>
                <h3 className="font-headline-md text-headline-md text-on-surface uppercase font-bold">
                  Confirm Paper Order Routing
                </h3>
              </div>
              <span className="px-2 py-0.5 bg-tertiary-fixed/10 border border-tertiary-fixed/30 text-tertiary-fixed text-xs">
                ALPACA PAPER ONLY
              </span>
            </div>

            <p className="font-body-sm text-body-sm text-on-surface-variant font-sans">
              You are about to route a defined-risk multi-leg order for <span className="font-bold text-on-surface font-mono">{decision.underlying} {strategy.name}</span> to the Alpaca Paper Trading environment.
            </p>

            {/* Structure Summary */}
            <div className="bg-surface p-4 rounded-sm border border-outline-variant/30 space-y-2">
              <div className="text-outline uppercase text-[10px] tracking-widest font-sans mb-2">
                Compiled MLEG Legs ({strategy.legs.length} Legs / 1 Contract)
              </div>
              {strategy.legs.map((leg) => (
                <div key={leg.id} className="flex justify-between items-center text-xs">
                  <span className={leg.side === 'BUY' ? 'text-on-surface' : 'text-primary font-bold'}>
                    {leg.side} 1x {leg.symbol} (${leg.strike} {leg.type})
                  </span>
                  <span className="text-on-surface-variant">
                    {leg.side === 'BUY' ? `-$${leg.mid.toFixed(2)}` : `+$${leg.mid.toFixed(2)}`}
                  </span>
                </div>
              ))}
            </div>

            {/* Financial Parameters */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-surface rounded-sm border border-primary/30">
                <span className="font-label-xs text-[10px] text-outline uppercase block font-sans">Max Profit</span>
                <span className="font-data-lg text-primary font-bold">${strategy.maxProfit.toFixed(2)}</span>
              </div>
              <div className="p-3 bg-surface rounded-sm border border-error/30">
                <span className="font-label-xs text-[10px] text-outline uppercase block font-sans">Max Risk (BP Req)</span>
                <span className="font-data-lg text-error font-bold">-${strategy.maxLoss.toFixed(2)}</span>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowConfirmModal(false)}
                className="px-5 py-2.5 border border-outline-variant hover:border-outline text-on-surface-variant font-data-md uppercase text-xs rounded-sm"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmApproval}
                className="px-6 py-2.5 bg-primary hover:bg-primary-fixed text-on-primary font-bold font-data-md uppercase text-xs shadow-glow-primary rounded-sm flex items-center gap-2"
              >
                <span>Confirm &amp; Route to Alpaca</span>
                <span className="material-symbols-outlined text-[16px]">send</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
