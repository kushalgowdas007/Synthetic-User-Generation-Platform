import React from 'react';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  let colorStyle = 'bg-slate-100 text-slate-700 border-slate-200';

  const s = status?.toLowerCase() || '';
  if (s.includes('recommended') || s.includes('high') || s.includes('valid')) {
    colorStyle = 'bg-teal-50 text-teal-700 border-teal-200';
  } else if (s.includes('planned') || s.includes('in progress')) {
    colorStyle = 'bg-blue-50 text-blue-700 border-blue-200';
  } else if (s.includes('completed') || s.includes('ready')) {
    colorStyle = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (s.includes('rejected') || s.includes('low') || s.includes('risk')) {
    colorStyle = 'bg-rose-50 text-rose-700 border-rose-200';
  } else if (s.includes('moderate') || s.includes('warning')) {
    colorStyle = 'bg-amber-50 text-amber-700 border-amber-200';
  }

  const sizeStyle = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center rounded-full font-semibold border ${sizeStyle} ${colorStyle}`}>
      {status}
    </span>
  );
};
