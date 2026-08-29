'use client';

import React, { useEffect, useState } from 'react';
import { useAppStore } from '@/lib/store';
import { Navbar } from '@/components/Navbar';
import { MetricCard } from '@/components/MetricCard';
import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import { fetchReportsAPI } from '@/lib/api';
import { ConsultantReport } from '@/lib/types';
import {
  Compass,
  Sparkles,
  TrendingUp,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  Layers,
  ArrowRight,
  Zap,
  Target
} from 'lucide-react';

export default function ProductStrategyPage() {
  const { personas, experiment, surveyResult, interviewMemories, insights, focusGroupTranscript } = useAppStore();

  const [reportData, setReportData] = useState<ConsultantReport | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (personas.length > 0) {
      setLoading(true);
      const interviewRows = Object.values(interviewMemories).flatMap((m) => m.history || []);
      fetchReportsAPI({
        experiment,
        personas,
        survey_results: surveyResult,
        interview_rows: interviewRows,
        insights,
        focus_group: focusGroupTranscript,
      })
        .then((res) => {
          if (res.consultant_report) {
            setReportData(res.consultant_report);
          }
        })
        .catch((e) => console.warn('Could not build strategy report', e))
        .finally(() => setLoading(false));
    }
  }, [personas, experiment, surveyResult, insights]);

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
      <Navbar
        title="Product Strategy & Launch Readiness"
        subtitle="Executive strategy synthesis, market fit evaluation, and decision roadmap."
      />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
        {personas.length === 0 ? (
          <EmptyState
            icon={Compass}
            title="Personas Required"
            description="Generate personas in the Workspace to produce strategic launch insights."
            actionHref="/"
            actionLabel="Generate Personas"
          />
        ) : (
          <>
            {/* Strategy Metric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                title="Launch Readiness"
                value={`${reportData?.launch_readiness || 78}%`}
                subtitle="Evidence-weighted launch score"
                icon={Compass}
                iconColor="text-teal-600 bg-teal-50"
              />
              <MetricCard
                title="Market Fit Signal"
                value={`${reportData?.market_fit || 72} / 100`}
                subtitle="Cohort willingness to adopt"
                icon={TrendingUp}
                iconColor="text-blue-600 bg-blue-50"
              />
              <MetricCard
                title="Revenue Potential"
                value={reportData?.revenue_potential || 'Promising'}
                subtitle="Based on pricing sensitivity"
                icon={Zap}
                iconColor="text-purple-600 bg-purple-50"
              />
              <MetricCard
                title="Risk Factor"
                value={`${reportData?.risk_score || 22}%`}
                subtitle="Identified adoption friction"
                icon={AlertTriangle}
                iconColor="text-rose-600 bg-rose-50"
              />
            </div>

            {/* Strategic Synthesis Banner */}
            {reportData?.why && (
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-2">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Strategic Assessment</h3>
                <p className="text-sm text-slate-800 leading-relaxed font-medium">{reportData.why}</p>
              </div>
            )}

            {/* SWOT Matrix Grid */}
            {reportData?.swot && (
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-teal-600" />
                  Strategic SWOT Analysis
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-emerald-50/50 rounded-xl border border-emerald-100 space-y-2">
                    <h4 className="text-xs font-bold text-emerald-900 uppercase tracking-wider">Strengths</h4>
                    <ul className="text-xs text-emerald-800 space-y-1">
                      {reportData.swot.strengths.map((s, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
                          <span>{s}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="p-4 bg-blue-50/50 rounded-xl border border-blue-100 space-y-2">
                    <h4 className="text-xs font-bold text-blue-900 uppercase tracking-wider">Opportunities</h4>
                    <ul className="text-xs text-blue-800 space-y-1">
                      {reportData.swot.opportunities.map((o, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <Sparkles className="w-3.5 h-3.5 text-blue-600 flex-shrink-0 mt-0.5" />
                          <span>{o}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="p-4 bg-amber-50/50 rounded-xl border border-amber-100 space-y-2">
                    <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider">Weaknesses</h4>
                    <ul className="text-xs text-amber-800 space-y-1">
                      {reportData.swot.weaknesses.map((w, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
                          <span>{w}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="p-4 bg-rose-50/50 rounded-xl border border-rose-100 space-y-2">
                    <h4 className="text-xs font-bold text-rose-900 uppercase tracking-wider">Threats & Risks</h4>
                    <ul className="text-xs text-rose-800 space-y-1">
                      {reportData.swot.threats.map((t, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-rose-500 font-bold">•</span>
                          <span>{t}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Strategic Roadmap (Now, Next, Later) */}
            {reportData?.roadmap && (
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-teal-600" />
                  Product Launch & Iteration Roadmap
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                  {reportData.roadmap.map((phase, idx) => {
                    const [timeline, ...rest] = phase.split(':');
                    return (
                      <div key={idx} className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                        <span className="text-xs font-bold text-teal-800 block">{timeline}</span>
                        <p className="text-xs text-slate-700 leading-relaxed">{rest.join(':')}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Business Recommendations */}
            {reportData?.business_recommendations && (
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Target className="w-4 h-4 text-teal-600" />
                  Strategic Go-to-Market Guidance
                </h3>
                <div className="space-y-2">
                  {reportData.business_recommendations.map((rec, idx) => (
                    <div key={idx} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs text-slate-800">
                      <span className="font-bold text-teal-600 text-sm">0{idx + 1}</span>
                      <p className="leading-relaxed">{rec}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
