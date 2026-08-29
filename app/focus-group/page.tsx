'use client';

import React, { useState } from 'react';
import { useAppStore } from '@/lib/store';
import { Navbar } from '@/components/Navbar';
import { EmptyState } from '@/components/EmptyState';
import { runFocusGroupAPI } from '@/lib/api';
import { FocusGroupTurn } from '@/lib/types';
import {
  Users2,
  Play,
  MessageSquare,
  Sparkles,
  ShieldCheck,
  UserCheck,
  CheckCircle2
} from 'lucide-react';

export default function FocusGroupPage() {
  const { personas, experiment, focusGroupTranscript, setFocusGroupTranscript } = useAppStore();

  const [moderatorQuestion, setModeratorQuestion] = useState<string>(
    'How do you currently solve workflow bottlenecks, and what would make you switch to this product?'
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunFocusGroup = async () => {
    if (personas.length === 0) {
      setError('Please generate personas first before running a focus group.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await runFocusGroupAPI({
        question: moderatorQuestion,
        personas,
        experiment,
      });
      setFocusGroupTranscript(res.transcript);
    } catch (err: any) {
      setError(err.message || 'Failed to simulate focus group');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
      <Navbar
        title="Focus Group Simulator"
        subtitle="Simulate multi-persona round-table discussions with moderator prompting and peer interaction."
      />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-6">
        {personas.length === 0 ? (
          <EmptyState
            icon={Users2}
            title="Personas Required"
            description="Generate personas in the Workspace to assemble a focus group cohort."
            actionHref="/"
            actionLabel="Generate Personas"
          />
        ) : (
          <>
            {/* Control Box */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
              <div>
                <h2 className="text-base font-bold text-slate-900">Moderator Prompt & Discussion Topic</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Pose an open-ended dilemma or value proposition to trigger synthetic cohort discourse.
                </p>
              </div>

              <div>
                <textarea
                  rows={2}
                  value={moderatorQuestion}
                  onChange={(e) => setModeratorQuestion(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-medium"
                  placeholder="Ask a question for the focus group participants to discuss..."
                />
              </div>

              {error && (
                <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs">
                  {error}
                </div>
              )}

              <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
                  <UserCheck className="w-3.5 h-3.5 text-teal-600" />
                  <span>Participants: {Math.min(6, personas.length)} synthetic personas</span>
                </div>

                <button
                  onClick={handleRunFocusGroup}
                  disabled={loading || !moderatorQuestion.trim()}
                  className="px-5 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-xs font-bold transition flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                      <span>Simulating Focus Group Discussion...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-current" />
                      <span>Start Focus Group</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Transcript Stream */}
            {focusGroupTranscript.length > 0 && (
              <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-teal-600" />
                    Discussion Transcript
                  </h3>
                  <span className="text-xs text-slate-500 font-medium">
                    {focusGroupTranscript.length} turns recorded
                  </span>
                </div>

                <div className="p-6 space-y-4 max-h-[500px] overflow-y-auto divide-y divide-slate-100">
                  {focusGroupTranscript.map((turn, idx) => {
                    const isModerator = turn.role === 'moderator';

                    return (
                      <div key={idx} className={`pt-4 first:pt-0 flex gap-4 items-start ${isModerator ? 'bg-slate-50 -mx-6 px-6 py-4 border-b border-slate-200' : ''}`}>
                        <div
                          className={`w-9 h-9 rounded-xl font-bold flex-shrink-0 flex items-center justify-center text-xs ${
                            isModerator
                              ? 'bg-slate-900 text-white'
                              : 'bg-teal-100 text-teal-800 border border-teal-200'
                          }`}
                        >
                          {isModerator ? 'M' : turn.speaker.charAt(0)}
                        </div>

                        <div className="flex-1 space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-xs text-slate-900">{turn.speaker}</span>
                            <span
                              className={`text-[10px] px-2 py-0.2 rounded font-semibold ${
                                isModerator
                                  ? 'bg-slate-200 text-slate-800'
                                  : 'bg-teal-50 text-teal-700'
                              }`}
                            >
                              {isModerator ? 'Moderator' : 'Participant'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-600 leading-relaxed">{turn.message}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
