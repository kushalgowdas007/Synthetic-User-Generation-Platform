import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  subMessage?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Processing request...',
  subMessage = 'Connecting to backend intelligence services',
}) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-12 text-center max-w-md mx-auto my-12 shadow-sm">
      <Loader2 className="w-10 h-10 text-teal-600 animate-spin mx-auto mb-4" />
      <h3 className="text-base font-bold text-slate-900">{message}</h3>
      <p className="text-xs text-slate-500 mt-1">{subMessage}</p>
    </div>
  );
};
