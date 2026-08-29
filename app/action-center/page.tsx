'use client';

import React, { useState, useEffect } from 'react';
import { useAppStore } from '@/lib/store';
import { Navbar } from '@/components/Navbar';
import { MetricCard } from '@/components/MetricCard';
import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import { fetchActionsAPI } from '@/lib/api';
import { ProductDecision } from '@/lib/types';
import {
  CheckSquare,
  Sparkles,
  Zap,
  Target,
  Clock,
  Layers,
  ArrowRight,
  TrendingUp,
  Sliders,
  CheckCircle2,
  AlertCircle,
  HelpCircle
} from 'lucide-react';

export default function ActionCenterPage() {
  const { personas, experiment, insights, surveyResult, actions, setActions } = useAppStore();

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('All');

  const handleGenerateActions = async () => {
    if (personas.length === 0) {
      setError('Please generate personas before producing product actions.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await fetchActionsAPI({
        experiment,
        personas,
        insights,
        survey_results: surveyResult,
      });
      setActions(res.actions);
    } catch (err: any) {
      setError(err.message || 'Failed to generate actions');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = (id: string, newStatus: ProductDecision['status']) => {
    setActions((prev) =>
      prev.map((act) => (act.id === id ? { ...act, status: newStatus } : act))
    );
  };

  const filteredActions = actions.filter(
    (act) => statusFilter === 'All' || act.status === statusFilter
  );

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
      <Navbar
        title="Action Center — What Should We Do Next?"
        subtitle="Prioritized, evidence-weighted product execution decisions derived directly from research."
      />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
        {personas.length === 0 ? (
          <EmptyState
            icon={CheckSquare}
            title="Personas Required"
            description="Generate personas in the Workspace to synthesize evidence-backed actions."
            actionHref="/"
            actionLabel="Generate Personas"
          />
        ) : (
          <>
            {/* Header Controls */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-slate-900">Decision Engine & Strategic Prioritization</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Automated weighted ranking: Impact (25%), Confidence (20%), Evidence (20%), Urgency (15%), Ease (20%).
                </p>
              </div>

              <button
                onClick={handleGenerateActions}
                disabled={loading}
                className="px-5 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-xs font-bold transition flex items-center gap-2 shadow-sm"
              >
                {loading ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    <span>Ranking Decisions...</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    <span>{actions.length > 0 ? 'Refresh Decisions' : 'Generate Product Actions'}</span>
                  </>
                )}
              </button>
            </div>

            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs">
                {error}
              </div>
            )}

            {/* Impact x Effort Matrix Visualization */}
            {actions.length > 0 && (
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <Target className="w-4 h-4 text-teal-600" />
                    Impact × Effort Matrix
                  </h3>
                  <span className="text-xs text-slate-500">
                    Quadrant mapping of prioritized roadmap actions
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  {/* Quick Wins: High Impact, Low Effort */}
                  <div className="p-4 bg-emerald-50/60 rounded-xl border border-emerald-200 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-emerald-900 uppercase tracking-wider">
                        ⭐ Quick Wins (High Impact / Low Effort)
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                        Top Priority
                      </span>
                    </div>
                    <div className="space-y-1.5 pt-1">
                      {actions
                        .filter((a) => a.impact >= 75 && a.effort <= 45)
                        .map((a, i) => (
                          <div key={i} className="p-2 bg-white rounded-lg border border-emerald-100 text-xs font-medium text-emerald-950 flex items-center justify-between">
                            <span className="truncate">{a.title}</span>
                            <span className="text-[10px] font-bold text-emerald-700 ml-2">P:{a.priority}</span>
                          </div>
                        ))}
                      {actions.filter((a) => a.impact >= 75 && a.effort <= 45).length === 0 && (
                        <p className="text-[11px] text-emerald-700 italic">No direct actions in this quadrant.</p>
                      )}
                    </div>
                  </div>

                  {/* Strategic Bets: High Impact, High Effort */}
                  <div className="p-4 bg-blue-50/60 rounded-xl border border-blue-200 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-blue-900 uppercase tracking-wider">
                        🚀 Strategic Bets (High Impact / High Effort)
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-800">
                        Major Projects
                      </span>
                    </div>
                    <div className="space-y-1.5 pt-1">
                      {actions
                        .filter((a) => a.impact >= 75 && a.effort > 45)
                        .map((a, i) => (
                          <div key={i} className="p-2 bg-white rounded-lg border border-blue-100 text-xs font-medium text-blue-950 flex items-center justify-between">
                            <span className="truncate">{a.title}</span>
                            <span className="text-[10px] font-bold text-blue-700 ml-2">P:{a.priority}</span>
                          </div>
                        ))}
                      {actions.filter((a) => a.impact >= 75 && a.effort > 45).length === 0 && (
                        <p className="text-[11px] text-blue-700 italic">No direct actions in this quadrant.</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Filter Tabs */}
            {actions.length > 0 && (
              <div className="flex items-center gap-2 overflow-x-auto text-xs pb-1">
                {['All', 'Recommended', 'Planned', 'In Progress', 'Completed', 'Rejected'].map((status) => (
                  <button
                    key={status}
                    onClick={() => setStatusFilter(status)}
                    className={`px-3 py-1.5 rounded-lg font-medium transition ${
                      statusFilter === status
                        ? 'bg-slate-900 text-white font-semibold'
                        : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    {status} ({status === 'All' ? actions.length : actions.filter((a) => a.status === status).length})
                  </button>
                ))}
              </div>
            )}

            {/* Action Cards List */}
            {filteredActions.length > 0 && (
              <div className="space-y-4">
                {filteredActions.map((action, idx) => (
                  <div key={idx} className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4 hover:border-slate-300 transition">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 font-bold flex items-center justify-center text-sm border border-teal-200">
                          {action.priority}
                        </div>
                        <div>
                          <h3 className="text-sm font-bold text-slate-900">{action.title}</h3>
                          <p className="text-xs text-slate-500 mt-0.5">{action.problem}</p>
                        </div>
                      </div>

                      {/* Status Selector */}
                      <div className="flex items-center gap-2">
                        <select
                          value={action.status}
                          onChange={(e) => handleStatusChange(action.id, e.target.value as any)}
                          className="px-2.5 py-1 text-xs rounded-lg border border-slate-200 bg-white font-semibold text-slate-700 focus:outline-none focus:border-teal-500"
                        >
                          <option value="Recommended">Recommended</option>
                          <option value="Planned">Planned</option>
                          <option value="In Progress">In Progress</option>
                          <option value="Completed">Completed</option>
                          <option value="Rejected">Rejected</option>
                        </select>
                        <StatusBadge status={action.status} size="sm" />
                      </div>
                    </div>

                    {/* Recommendation Box */}
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700">
                      <span className="font-semibold text-slate-900 block mb-0.5">Recommendation:</span>
                      {action.recommendation}
                    </div>

                    {/* Metrics Bar */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-slate-50/50 p-3 rounded-lg border border-slate-100">
                      <div>
                        <span className="text-[11px] text-slate-500 block">Impact</span>
                        <span className="font-bold text-emerald-700">{action.impact}/100</span>
                      </div>
                      <div>
                        <span className="text-[11px] text-slate-500 block">Effort</span>
                        <span className="font-bold text-amber-700">{action.effort}/100</span>
                      </div>
                      <div>
                        <span className="text-[11px] text-slate-500 block">Confidence</span>
                        <span className="font-bold text-teal-700">{action.confidence}%</span>
                      </div>
                      <div>
                        <span className="text-[11px] text-slate-500 block">Evidence Strength</span>
                        <span className="font-bold text-blue-700">{action.evidence_strength || 85}%</span>
                      </div>
                    </div>

                    {/* Footer: Personas & Expected Outcomes */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-2 border-t border-slate-100">
                      <div>
                        <span className="text-[11px] font-semibold text-slate-500 block mb-1">Target Personas:</span>
                        <div className="flex flex-wrap gap-1">
                          {(action.affected_personas || []).map((name, pIdx) => (
                            <span key={pIdx} className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">
                              {name}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className="text-[11px] font-semibold text-slate-500 block mb-1">Expected Outcome:</span>
                        <ul className="text-[11px] text-slate-600 space-y-0.5">
                          {(action.expected_outcomes || []).map((out, oIdx) => (
                            <li key={oIdx} className="flex items-center gap-1.5">
                              <CheckCircle2 className="w-3 h-3 text-emerald-600 flex-shrink-0" />
                              <span>{out}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
