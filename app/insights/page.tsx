'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/lib/store';
import { Navbar } from '@/components/Navbar';
import { MetricCard } from '@/components/MetricCard';
import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import { fetchInsightsAPI } from '@/lib/api';
import { StructuredInsight } from '@/lib/types';
import {
  Lightbulb,
  Sparkles,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  BrainCircuit,
  ArrowRight,
  ShieldCheck,
  Tag,
  PlusCircle,
  BarChart3
} from 'lucide-react';

export default function InsightsPage() {
  const router = useRouter();
  const {
    personas,
    experiment,
    surveyResult,
    interviewMemories,
    focusGroupTranscript,
    insights,
    setInsights,
    actions,
    setActions,
  } = useAppStore();

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSynthesizeInsights = async () => {
    if (personas.length === 0) {
      setError('Please generate personas before synthesizing insights.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      // Gather interview history
      const interviewRows = Object.values(interviewMemories).flatMap((m) => m.history || []);

      const res = await fetchInsightsAPI({
        personas,
        survey_results: surveyResult,
        interview_results: interviewRows,
        focus_group_results: focusGroupTranscript,
        experiment,
      });

      setInsights(res);
    } catch (err: any) {
      setError(err.message || 'Failed to synthesize insights');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateActionFromInsight = (insight: StructuredInsight) => {
    const newAction = {
      id: `act_${Date.now()}`,
      title: insight.recommendation || `Address ${insight.title}`,
      problem: insight.title,
      recommendation: insight.recommendation || 'Implement workflow improvements based on evidence.',
      priority: Math.round(insight.severity_or_importance * 0.9),
      impact: insight.severity_or_importance,
      effort: 35,
      confidence: insight.confidence,
      evidence_strength: insight.confidence,
      urgency: 75,
      affected_personas: insight.affected_personas || [],
      expected_outcomes: ['Improve cohort adoption', 'Address critical friction points'],
      source_insights: [insight.title],
      status: 'Planned' as const,
    };

    setActions((prev) => [newAction, ...prev]);
    router.push('/action-center');
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
      <Navbar
        title="Research Insights Engine"
        subtitle="Extract evidence-traceable thematic clusters, sentiment drivers, and UX risks."
      />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
        {personas.length === 0 ? (
          <EmptyState
            icon={Lightbulb}
            title="Personas Required"
            description="Generate personas in the Workspace to synthesize evidence-backed insights."
            actionHref="/"
            actionLabel="Generate Personas"
          />
        ) : (
          <>
            {/* Top Action Header */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-slate-900">Multi-Modal Research Synthesis</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Triangulates survey responses, 1-on-1 interview memories, and focus group dialogues.
                </p>
              </div>

              <button
                onClick={handleSynthesizeInsights}
                disabled={loading}
                className="px-5 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-xs font-bold transition flex items-center gap-2 shadow-sm"
              >
                {loading ? (
                  <>
                    <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    <span>Extracting Evidence Clusters...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>{insights ? 'Re-Synthesize Insights' : 'Synthesize Research Insights'}</span>
                  </>
                )}
              </button>
            </div>

            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs">
                {error}
              </div>
            )}

            {/* Insights Display */}
            {insights && (
              <div className="space-y-8">
                {/* Metric Summary */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <MetricCard
                    title="Overall Product Fit"
                    value={`${insights.product_fit_score?.toFixed(1) || 65} / 100`}
                    subtitle="Validation confidence score"
                    icon={TrendingUp}
                  />
                  <MetricCard
                    title="Recommendation Score"
                    value={`${insights.recommendation_score?.toFixed(1) || 70} / 100`}
                    subtitle="Simulated referral likelihood"
                    icon={BarChart3}
                    iconColor="text-blue-600 bg-blue-50"
                  />
                  <MetricCard
                    title="Identified Themes"
                    value={insights.themes?.length || 0}
                    subtitle="Top cognitive drivers"
                    icon={BrainCircuit}
                    iconColor="text-purple-600 bg-purple-50"
                  />
                  <MetricCard
                    title="Extracted Insights"
                    value={insights.structured_insights?.length || 0}
                    subtitle="Evidence-backed clusters"
                    icon={Lightbulb}
                    iconColor="text-emerald-600 bg-emerald-50"
                  />
                </div>

                {/* Executive Summary Card */}
                {insights.executive_summary && (
                  <div className="bg-gradient-to-r from-teal-900 to-slate-900 text-white p-6 rounded-xl shadow-sm space-y-2">
                    <h3 className="text-xs font-bold text-teal-400 uppercase tracking-wider">Executive Synthesis</h3>
                    <p className="text-sm text-slate-200 leading-relaxed font-normal">{insights.executive_summary}</p>
                  </div>
                )}

                {/* Themes & Pain Points Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Thematic Clusters */}
                  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <Tag className="w-4 h-4 text-teal-600" />
                      Key Thematic Drivers
                    </h3>
                    <div className="space-y-2.5">
                      {(insights.themes || []).map((t, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                          <span className="font-semibold text-slate-800">{t.theme}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-[11px] text-slate-500">{t.count} mentions</span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-teal-50 text-teal-700 border border-teal-200">
                              {t.confidence_score}% conf
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Top Pain Points */}
                  <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-rose-600" />
                      Persona Pain Points & Blockers
                    </h3>
                    <div className="space-y-2.5">
                      {(insights.pain_points || []).map((p, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-rose-50/50 rounded-lg border border-rose-100 text-xs">
                          <span className="font-medium text-rose-900">{p.pain_point}</span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-white text-rose-700 border border-rose-200">
                            {p.count} affected
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Structured Evidence-Traceable Insights */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-base font-bold text-slate-900">Structured Evidence-Traceable Insights</h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Each insight cites exact evidence points, confidence intervals, and affected personas.
                      </p>
                    </div>
                    <button
                      onClick={() => router.push('/action-center')}
                      className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold flex items-center gap-2 transition"
                    >
                      <span>Open Action Center</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {(insights.structured_insights || []).map((ins, idx) => (
                      <div key={idx} className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4 flex flex-col justify-between">
                        <div className="space-y-3">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <StatusBadge status={ins.type || 'Insight'} size="sm" />
                              <h4 className="text-sm font-bold text-slate-900 mt-1.5">{ins.title}</h4>
                            </div>
                            <div className="text-right flex-shrink-0">
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-teal-50 text-teal-700 border border-teal-200">
                                {ins.confidence}% Confidence
                              </span>
                            </div>
                          </div>

                          {ins.recommendation && (
                            <div className="p-3 bg-teal-50/60 rounded-lg border border-teal-100 text-xs text-teal-950 font-medium">
                              <span className="font-bold block text-teal-800 text-[11px]">Recommended Action:</span>
                              {ins.recommendation}
                            </div>
                          )}

                          {/* Evidence Citation */}
                          {ins.evidence && ins.evidence.length > 0 && (
                            <div className="space-y-1.5 pt-2 border-t border-slate-100 text-[11px]">
                              <span className="font-semibold text-slate-700 block">Evidence Citation:</span>
                              {ins.evidence.map((ev, eIdx) => (
                                <div key={eIdx} className="bg-slate-50 p-2 rounded text-slate-600 border border-slate-100">
                                  <span className="font-medium text-slate-800">[{ev.source_type}]:</span> {ev.metric_or_quote}
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Affected Personas */}
                          {ins.affected_personas && ins.affected_personas.length > 0 && (
                            <div className="flex items-center gap-1.5 flex-wrap pt-1">
                              <span className="text-[10px] font-semibold text-slate-500">Affected:</span>
                              {ins.affected_personas.map((name, pIdx) => (
                                <span key={pIdx} className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">
                                  {name}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Convert to Action Button */}
                        <div className="pt-3 border-t border-slate-100">
                          <button
                            onClick={() => handleCreateActionFromInsight(ins)}
                            className="w-full py-2 px-3 rounded-lg border border-teal-300 hover:bg-teal-50 text-teal-700 text-xs font-semibold flex items-center justify-center gap-1.5 transition"
                          >
                            <PlusCircle className="w-3.5 h-3.5" />
                            <span>Create Product Action</span>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
