'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';

interface NavItem {
  label: string;
  href: string;
  matchPrefix?: string;
  icon: string;
  exact?: boolean;
}

const MAIN_TERMINAL_ITEMS: NavItem[] = [
  { label: 'Command Center', href: '/terminal', icon: 'terminal', exact: true },
  { label: 'Autonomous Agents', href: '/agents', icon: 'smart_toy' },
  { label: 'Live Portfolio', href: '/portfolio', icon: 'account_balance_wallet' },
  { label: 'Volatility Surface', href: '/surface', icon: 'monitoring' },
  { label: 'Opportunity Scanner', href: '/tournament', icon: 'radar' },
  { label: 'Decision Room', href: '/decision/DEC-SPY-9942', matchPrefix: '/decision', icon: 'gavel' },
  { label: 'Payoff & Stress Lab', href: '/stress', icon: 'science' },
];

const ANALYSIS_OPS_ITEMS: NavItem[] = [
  { label: 'AI Agent Trace', href: '/trace/DEC-SPY-9942', matchPrefix: '/trace', icon: 'account_tree' },
  { label: 'Decision History', href: '/history', icon: 'history' },
  { label: 'Replay Mode', href: '/replay/AFP-1024', matchPrefix: '/replay', icon: 'replay' },
  { label: 'Counterfactual Lab', href: '/counterfactual', icon: 'science' },
];

export const AppSidebar: React.FC = () => {
  const pathname = usePathname();

  const isItemActive = (item: NavItem) => {
    if (item.matchPrefix) {
      return pathname.startsWith(item.matchPrefix);
    }
    if (item.exact) {
      return pathname === item.href;
    }
    return pathname.startsWith(item.href.split('?')[0]);
  };

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-surface-container-low border-r border-outline-variant/30 z-50 flex flex-col select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-panel-padding gap-3 border-b border-outline-variant/20">
        <div className="relative w-8 h-8 flex items-center justify-center">
          <Image
            src="/assets/voltron-logo.png"
            alt="VOLTRON Logo"
            width={32}
            height={32}
            className="object-contain"
            priority
          />
        </div>
        <div className="flex flex-col">
          <span className="font-headline-md text-headline-md text-primary font-bold tracking-tighter">
            VOLTRON
          </span>
          <span className="text-[9px] font-mono tracking-widest text-outline uppercase -mt-1">
            ALPHA OPTIONS
          </span>
        </div>
      </div>

      {/* Navigation Groups */}
      <nav className="flex-1 py-4 overflow-y-auto space-y-6">
        {/* Main Terminal Section */}
        <div>
          <div className="px-4 mb-2 text-label-xs font-label-xs text-outline uppercase tracking-widest">
            Main Terminal
          </div>
          <div className="space-y-1">
            {MAIN_TERMINAL_ITEMS.map((item) => {
              const active = isItemActive(item);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-4 py-2.5 mx-2 rounded-sm transition-all group ${
                    active
                      ? 'bg-secondary-container text-on-secondary-container font-semibold shadow-sm'
                      : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                  }`}
                >
                  <span
                    className={`material-symbols-outlined text-[20px] ${
                      active ? 'text-on-secondary-container' : 'text-outline-variant group-hover:text-primary'
                    }`}
                  >
                    {item.icon}
                  </span>
                  <span className="font-data-md text-data-md">{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Analysis & Ops Section */}
        <div>
          <div className="px-4 mb-2 text-label-xs font-label-xs text-outline uppercase tracking-widest">
            Analysis & Ops
          </div>
          <div className="space-y-1">
            {ANALYSIS_OPS_ITEMS.map((item) => {
              const active = isItemActive(item);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-4 py-2.5 mx-2 rounded-sm transition-all group ${
                    active
                      ? 'bg-secondary-container text-on-secondary-container font-semibold shadow-sm'
                      : 'text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface'
                  }`}
                >
                  <span
                    className={`material-symbols-outlined text-[20px] ${
                      active ? 'text-on-secondary-container' : 'text-outline-variant group-hover:text-primary'
                    }`}
                  >
                    {item.icon}
                  </span>
                  <span className="font-data-md text-data-md">{item.label}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </nav>

      {/* System Build Tag */}
      <div className="p-3 border-t border-outline-variant/20 bg-surface-container-lowest flex items-center justify-between text-[10px] font-mono text-outline">
        <span>RUNTIME V0.9.4</span>
        <span className="text-primary-fixed-dim">PERSON 2 ACTIVE</span>
      </div>
    </aside>
  );
};
