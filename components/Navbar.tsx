'use client';

import React from 'react';
import { useAppStore } from '@/lib/store';
import { Sparkles, RotateCcw, ShieldCheck, Box } from 'lucide-react';

interface NavbarProps {
  title: string;
  subtitle?: string;
}

export const Navbar: React.FC<NavbarProps> = ({ title, subtitle }) => {
  const { experiment, personas, resetAll } = useAppStore();

  return (
    <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between sticky top-0 z-20">
      <div>
        <h1 className="text-xl font-bold text-slate-900 tracking-tight">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {experiment.product_name && (
          <div className="hidden md:flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-700">
            <Box className="w-3.5 h-3.5 text-teal-600" />
            <span className="font-semibold">{experiment.product_name}</span>
            <span className="text-slate-400">|</span>
            <span className="text-slate-500">{personas.length} personas loaded</span>
          </div>
        )}

        <button
          onClick={resetAll}
          title="Reset workspace"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 text-xs font-medium transition"
        >
          <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
          <span>Reset Session</span>
        </button>
      </div>
    </header>
  );
};
