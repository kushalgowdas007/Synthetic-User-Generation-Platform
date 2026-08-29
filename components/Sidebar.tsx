'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Users,
  ClipboardList,
  MessageSquare,
  Users2,
  Lightbulb,
  CheckSquare,
  Compass,
  Sliders,
  BarChart3,
  FileText,
  Sparkles,
  FlaskConical
} from 'lucide-react';
import { useAppStore } from '@/lib/store';

const navItems = [
  { href: '/', label: 'Home / Workspace', icon: LayoutDashboard },
  { href: '/personas', label: 'Persona Lab', icon: Users, badgeKey: 'personas' },
  { href: '/survey', label: 'Survey', icon: ClipboardList, badgeKey: 'survey' },
  { href: '/interview', label: 'Interview', icon: MessageSquare },
  { href: '/focus-group', label: 'Focus Group', icon: Users2 },
  { href: '/insights', label: 'Insights', icon: Lightbulb, badgeKey: 'insights' },
  { href: '/action-center', label: 'Action Center', icon: CheckSquare, badgeKey: 'actions' },
  { href: '/product-strategy', label: 'Product Strategy', icon: Compass },
  { href: '/experiment-simulator', label: 'Experiment Simulator', icon: Sliders },
  { href: '/dashboard', label: 'Dashboard', icon: BarChart3 },
  { href: '/reports', label: 'Reports', icon: FileText },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { personas, surveyResult, insights, actions } = useAppStore();

  const getBadge = (key?: string) => {
    if (key === 'personas' && personas.length > 0) return personas.length;
    if (key === 'survey' && surveyResult) return 'Done';
    if (key === 'insights' && insights) return 'Ready';
    if (key === 'actions' && actions.length > 0) return actions.length;
    return null;
  };

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0 min-h-screen border-r border-slate-800">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-teal-500 flex items-center justify-center text-slate-950 shadow-lg shadow-teal-500/20 font-bold text-lg">
            <FlaskConical className="w-6 h-6 text-slate-950" />
          </div>
          <div>
            <h1 className="font-bold text-white text-base tracking-tight leading-tight">
              AI Research Studio
            </h1>
            <p className="text-[11px] text-teal-400 font-medium leading-none mt-1">
              Synthetic Users to Decisions
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-300">
          Core Workflows
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          const badge = getBadge(item.badgeKey);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-teal-500/15 text-teal-300 font-semibold border-l-2 border-teal-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-teal-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {badge && (
                <span
                  className={`text-[11px] px-2 py-0.5 rounded-full font-semibold ${
                    typeof badge === 'number'
                      ? 'bg-teal-500/20 text-teal-300'
                      : 'bg-emerald-500/20 text-emerald-300'
                  }`}
                >
                  {badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800 text-xs text-slate-300">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            FastAPI Serverless
          </span>
          <span className="font-mono text-[10px] text-slate-300">v1.0.0</span>
        </div>
      </div>
    </aside>
  );
};
