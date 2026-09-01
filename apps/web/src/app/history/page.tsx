'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { HistoricalDecisionSummary } from '@/types/voltron';
import { DEMO_DECISION_HISTORY } from '@/fixtures/voltronFixtures';

export default function DecisionHistoryPage() {
  const [historyItems, setHistoryItems] = useState<HistoricalDecisionSummary[]>(DEMO_DECISION_HISTORY);
  const [selectedId, setSelectedId] = useState<string>('HIST-001');

  useEffect(() => {
    let isMounted = true;
    api.getHistoricalDecisions().then((data) => {
      if (isMounted) {
        setHistoryItems(data);
        if (data.length > 0) setSelectedId(data[0].id);
      }
    });
    return () => {
      isMounted = false;
    };
  }, []);

  const selectedItem = historyItems.find((h) => h.id === selectedId) || historyItems[0];

  const totalDecisions = historyItems.length;
  const approvedCount = historyItems.filter((h) => h.decision === "Approved").length;
  const approvalRate = totalDecisions > 0 ? ((approvedCount / totalDecisions) * 100).toFixed(1) : "0.0";
  const totalRisk = historyItems.reduce((acc, h) => acc + (h.riskAmount || 0), 0);
  const netOutcome = historyItems.reduce((acc, h) => acc + (h.isProfit ? h.outcomeAmount : -(h.riskAmount || 0)), 0);

  return (
    <div className="flex flex-col w-full gap-container-gap pb-container-gap">
      {/* Top Visual Summary Metrics */}
      <div className="grid grid-cols-2 gap-container-gap h-24">
        <div className="bg-surface-container flex items-center justify-between p-6 relative overflow-hidden rounded-sm border border-outline-variant/20">
          <div className="flex flex-col z-10">
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-widest mb-1">
              Session Decisions
            </span>
            <span className="font-display-lg text-display-lg text-on-surface font-mono font-bold">
              {totalDecisions}
            </span>
          </div>
          <div className="flex flex-col items-end z-10">
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-widest mb-1">
              Approval Rate
            </span>
            <span className="font-headline-md text-headline-md text-primary-fixed font-mono font-bold">
              {approvalRate}%
            </span>
          </div>
        </div>

        <div className="bg-surface-container flex items-center justify-between p-6 relative overflow-hidden rounded-sm border border-outline-variant/20">
          <div className="flex flex-col z-10">
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-widest mb-1">
              Total Risk Deployed
            </span>
            <span className="font-display-lg text-display-lg text-on-surface font-mono font-bold">
              ${totalRisk.toLocaleString()}
            </span>
          </div>
          <div className="flex flex-col items-end z-10">
            <span className="font-label-xs text-label-xs text-on-surface-variant uppercase tracking-widest mb-1">
              Net Outcome
            </span>
            <span className={`font-headline-md text-headline-md font-mono font-bold ${netOutcome >= 0 ? 'text-primary-fixed' : 'text-error'}`}>
              {netOutcome >= 0 ? `+$${netOutcome.toLocaleString()}` : `-$${Math.abs(netOutcome).toLocaleString()}`}
            </span>
          </div>
        </div>
      </div>

      {/* Main Ledger Split */}
      <div className="flex w-full gap-container-gap h-[calc(100vh-14rem)] min-h-[480px]">
        {/* Ledger Table (Left Panel) */}
        <div className="flex-grow flex flex-col gap-gutter bg-surface-container rounded-sm border border-outline-variant/20 overflow-hidden">
          {/* Table Header */}
          <div className="grid grid-cols-[120px_80px_160px_120px_100px_100px_1fr] items-center px-6 py-4 bg-surface-container-low border-b border-outline-variant/20 font-label-xs text-label-xs text-on-surface-variant uppercase font-mono">
            <span>Time</span>
            <span>Symbol</span>
            <span>Strategy</span>
            <span>Decision</span>
            <span className="text-right">Risk</span>
            <span className="text-right">Result</span>
            <span />
          </div>

          {/* Rows */}
          <div className="flex-1 overflow-y-auto font-mono">
            {historyItems.map((item) => {
              const isSelected = item.id === selectedId;
              const isApproved = item.decision === 'Approved';
              const isRejected = item.decision === 'Rejected';

              return (
                <div
                  key={item.id}
                  onClick={() => setSelectedId(item.id)}
                  className={`grid grid-cols-[120px_80px_160px_120px_100px_100px_1fr] items-center px-6 py-4 relative cursor-pointer transition-colors border-b border-outline-variant/10 ${
                    isSelected ? 'bg-surface-container-high' : 'hover:bg-surface-container-high/60 bg-surface-container'
                  }`}
                >
                  {isSelected && (
                    <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-primary shadow-glow-primary" />
                  )}
                  <span className="font-data-md text-data-md text-on-surface">{item.timeFormatted}</span>
                  <span className="font-data-md text-data-md text-on-surface font-bold">{item.symbol}</span>
                  <span className="font-data-md text-data-md text-on-surface">{item.strategyName}</span>
                  <div>
                    <span
                      className={`inline-flex items-center justify-center px-2 py-0.5 rounded-sm font-label-xs text-label-xs uppercase ${
                        isApproved
                          ? 'bg-primary-fixed/10 text-primary-fixed border border-primary/30'
                          : isRejected
                          ? 'bg-error-container/20 text-error border border-error/30'
                          : 'bg-surface-variant text-on-surface-variant'
                      }`}
                    >
                      {item.decision}
                    </span>
                  </div>
                  <span className="font-data-md text-data-md text-on-surface text-right">
                    {item.riskAmount > 0 ? `$${item.riskAmount}` : '--'}
                  </span>
                  <span
                    className={`font-data-md text-data-md text-right font-bold ${
                      item.outcomeAmount > 0 ? 'text-primary-fixed' : 'text-on-surface-variant'
                    }`}
                  >
                    {item.outcomeAmount > 0 ? `+$${item.outcomeAmount}` : '--'}
                  </span>
                  <div className="flex justify-end text-primary-fixed">
                    <span className="material-symbols-outlined text-[16px]">chevron_right</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Selected Decision Detail Card (Right Panel) */}
        {selectedItem && (
          <div className="w-[420px] flex flex-col gap-container-gap shrink-0">
            <div className="bg-surface-container p-6 rounded-sm border border-outline-variant/20 shadow-sm flex flex-col relative overflow-hidden">
              <div className="flex justify-between items-start mb-6 z-10">
                <div className="flex flex-col">
                  <span className="font-label-xs text-label-xs text-primary-fixed uppercase tracking-widest mb-1 font-mono">
                    Decision Details
                  </span>
                  <span className="font-display-lg text-display-lg text-on-surface leading-none font-bold">
                    {selectedItem.symbol}
                  </span>
                  <span className="font-body-sm text-body-sm text-on-surface-variant mt-1 font-mono">
                    {selectedItem.strategyName} ({selectedItem.legsSummary})
                  </span>
                </div>
                <span className="font-data-sm text-data-sm text-on-surface-variant bg-surface px-2 py-1 rounded-sm border border-outline-variant/20 font-mono">
                  {selectedItem.timeFormatted}
                </span>
              </div>

              {/* Metric Grid */}
              <div className="grid grid-cols-2 gap-px bg-surface-variant z-10 rounded-sm overflow-hidden font-mono">
                <div className="bg-surface-container flex flex-col p-3">
                  <span className="font-label-xs text-label-xs text-on-surface-variant uppercase mb-1 font-sans">
                    Max Risk
                  </span>
                  <span className="font-data-lg text-data-lg text-on-surface font-bold">
                    ${selectedItem.riskAmount}.00
                  </span>
                </div>
                <div className="bg-surface-container flex flex-col p-3">
                  <span className="font-label-xs text-label-xs text-on-surface-variant uppercase mb-1 font-sans">
                    POP
                  </span>
                  <span className="font-data-lg text-data-lg text-primary-fixed font-bold">
                    {(selectedItem.pop * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                <Link
                  href={`/decision/${selectedItem.id}`}
                  className="flex-1 bg-primary text-on-primary font-data-md text-data-md py-2 flex items-center justify-center gap-2 hover:bg-primary-fixed transition-colors rounded-sm font-bold uppercase"
                >
                  <span className="material-symbols-outlined text-[18px]">receipt_long</span>
                  View Ticket
                </Link>
                <Link
                  href="/counterfactual"
                  className="flex-1 border border-primary text-primary font-data-md text-data-md py-2 flex items-center justify-center gap-2 hover:bg-primary/10 transition-colors rounded-sm font-mono"
                >
                  <span className="material-symbols-outlined text-[18px]">science</span>
                  Counterfactual
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
