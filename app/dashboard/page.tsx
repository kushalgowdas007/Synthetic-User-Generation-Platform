'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/lib/store';
import { Navbar } from '@/components/Navbar';
import { MetricCard } from '@/components/MetricCard';
import { EmptyState } from '@/components/EmptyState';
import {
  BarChart3,
  Users,
  TrendingUp,
  MessageSquare,
  ClipboardList,
  CheckSquare,
  Sparkles,
  PieChart,
  Activity,
  Layers,
  ArrowRight
} from 'lucide-react';

export default function DashboardPage() {
  const router = useRouter();
  const { personas, experiment, surveyResult, interviewMemories, insights, actions } = useAppStore();

  const totalInterviewMessages = Object.values(interviewMemories).reduce(
    (acc, m) => acc + (m.history?.length || 0),
    0
  );

  const avgAge =
    personas.length > 0
      ? Math.round(personas.reduce((acc, p) => acc + (p.age || 30), 0) / personas.length)
      : 0;

  const avgQuality =
    personas.length > 0
      ? Math.round(personas.reduce((acc, p) => acc + (p.quality_score || 90), 0) / personas.length)
      : 0;

  const completedActions = actions.filter((a) => a.status === 'Completed').length;

  // Gender Breakdown
  const genderCounts: Record<string, number> = {};
  personas.forEach((p) => {
    const g = p.gender || 'Unknown';
    genderCounts[g] = (genderCounts[g] || 0) + 1;
  });

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
      <Navbar
        title="Intelligence Dashboard"
        subtitle="Holistic analytics overview across synthetic user generation, sentiment distribution, and strategic actions."
      />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
        {personas.length === 0 ? (
          <EmptyState
            icon={BarChart3}
            title="Personas Required"
            description="Generate a persona cohort in the Workspace to populate the research analytics dashboard."
            actionHref="/"
            actionLabel="Generate Personas"
          />
        ) : (
          <>
            {/* Top 4 Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                title="Total Personas"
                value={personas.length}
                subtitle={`Avg Age: ${avgAge} y/o`}
                icon={Users}
              />
              <MetricCard
                title="Product Fit Score"
                value={`${(surveyResult?.product_fit_score || insights?.product_fit_score || 68).toFixed(1)} / 100`}
                subtitle="Aggregated fit index"
                icon={TrendingUp}
                iconColor="text-teal-600 bg-teal-50"
              />
              <MetricCard
                title="Persona Quality Score"
                value={`${avgQuality} / 100`}
                subtitle="Faker & psych score"
                icon={Sparkles}
                iconColor="text-purple-600 bg-purple-50"
              />
              <MetricCard
                title="Actions Tracked"
                value={actions.length}
                subtitle={`${completedActions} completed`}
                icon={CheckSquare}
                iconColor="text-emerald-600 bg-emerald-50"
              />
            </div>

            {/* Sub Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Survey Responses</span>
                  <h4 className="text-xl font-bold text-slate-900 mt-1">{surveyResult?.responses?.length || 0}</h4>
                </div>
                <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                  <ClipboardList className="w-5 h-5" />
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Interview Turns</span>
                  <h4 className="text-xl font-bold text-slate-900 mt-1">{totalInterviewMessages}</h4>
                </div>
                <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
                  <MessageSquare className="w-5 h-5" />
                </div>
              </div>

              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Recommendation Index</span>
                  <h4 className="text-xl font-bold text-slate-900 mt-1">
                    {(insights?.recommendation_score || 72).toFixed(1)} / 100
                  </h4>
                </div>
                <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <Activity className="w-5 h-5" />
                </div>
              </div>
            </div>

            {/* Visual Charts & Breakdown Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Gender & Demographic Breakdown */}
              <div className="lg:col-span-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <PieChart className="w-4 h-4 text-teal-600" />
                  Cohort Demographics
                </h3>
                <div className="space-y-3 pt-2">
                  {Object.entries(genderCounts).map(([gender, count]) => {
                    const pct = Math.round((count / personas.length) * 100);
                    return (
                      <div key={gender} className="space-y-1">
                        <div className="flex justify-between text-xs text-slate-700">
                          <span className="font-medium">{gender}</span>
                          <span className="font-bold">{count} ({pct}%)</span>
                        </div>
                        <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                          <div className="bg-teal-500 h-full rounded-full" style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Top Themes & Sentiments */}
              <div className="lg:col-span-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-teal-600" />
                  Thematic Drivers
                </h3>
                {insights?.themes && insights.themes.length > 0 ? (
                  <div className="space-y-2.5 pt-2">
                    {insights.themes.slice(0, 5).map((t, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg text-xs">
                        <span className="font-semibold text-slate-800">{t.theme}</span>
                        <span className="text-teal-700 font-bold">{t.count} mentions</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic pt-4 text-center">
                    Synthesize insights to populate thematic analytics.
                  </p>
                )}
              </div>

              {/* Action Pipeline Breakdown */}
              <div className="lg:col-span-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <CheckSquare className="w-4 h-4 text-teal-600" />
                  Action Pipeline Status
                </h3>
                <div className="space-y-2 pt-2">
                  {['Recommended', 'Planned', 'In Progress', 'Completed'].map((status) => {
                    const count = actions.filter((a) => a.status === status).length;
                    return (
                      <div key={status} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg text-xs">
                        <span className="text-slate-700 font-medium">{status}</span>
                        <span className="font-bold text-slate-900">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Quick Navigation Footer */}
            <div className="p-6 bg-slate-900 text-white rounded-xl shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <h4 className="text-sm font-bold">Ready to export executive reports?</h4>
                <p className="text-xs text-slate-400 mt-0.5">
                  Compile complete research findings into a comprehensive executive PDF or Markdown document.
                </p>
              </div>
              <button
                onClick={() => router.push('/reports')}
                className="px-4 py-2.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-bold transition flex items-center gap-2"
              >
                <span>Generate Full Report</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
