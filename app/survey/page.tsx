'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/lib/store';
import { Navbar } from '@/components/Navbar';
import { MetricCard } from '@/components/MetricCard';
import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import { fetchSurveyTemplates, runSurveyAPI } from '@/lib/api';
import {
  ClipboardList,
  Play,
  Layers,
  Sparkles,
  BarChart2,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  HelpCircle
} from 'lucide-react';

export default function SurveyPage() {
  const router = useRouter();
  const { personas, experiment, surveyResult, setSurveyResult } = useAppStore();

  const [templates, setTemplates] = useState<string[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('Product Adoption');
  const [researchGoal, setResearchGoal] = useState<string>('Evaluate usability, value perception, and pricing sensitivity');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSurveyTemplates()
      .then((data) => {
        if (data.templates && data.templates.length > 0) {
          setTemplates(data.templates);
          setSelectedTemplate(data.templates[0]);
        }
      })
      .catch((e) => console.warn('Could not fetch templates', e));
  }, []);

  const handleRunSurvey = async () => {
    if (personas.length === 0) {
      setError('Please generate personas first before running a survey.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await runSurveyAPI({
        personas,
        product_name: experiment.product_name || 'the product',
        research_goal: researchGoal,
        template: selectedTemplate,
      });
      setSurveyResult(res);
    } catch (err: any) {
      setError(err.message || 'Survey execution failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
      <Navbar
        title="Survey Engine"
        subtitle="Simulate targeted quantitative & qualitative questionnaire runs across your synthetic persona cohort."
      />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
        {personas.length === 0 ? (
          <EmptyState
            icon={ClipboardList}
            title="Personas Required"
            description="You must generate or load a persona cohort in the Workspace before executing a synthetic survey."
            actionHref="/"
            actionLabel="Generate Personas"
          />
        ) : (
          <>
            {/* Top Control Panel */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-5">
                <div>
                  <h2 className="text-base font-bold text-slate-900">Survey Configuration</h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Select a standardized research template and specify your evaluation goal.
                  </p>
                </div>
                <div className="text-xs text-slate-500 font-medium">
                  Cohort size: <span className="font-bold text-teal-600">{personas.length} personas</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                    Survey Template
                  </label>
                  <select
                    value={selectedTemplate}
                    onChange={(e) => setSelectedTemplate(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 font-medium"
                  >
                    {templates.length > 0 ? (
                      templates.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))
                    ) : (
                      <>
                        <option value="Product Adoption">Product Adoption</option>
                        <option value="Pricing and Value">Pricing and Value</option>
                        <option value="Usability and Trust">Usability and Trust</option>
                      </>
                    )}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                    Research Objective / Context
                  </label>
                  <input
                    type="text"
                    value={researchGoal}
                    onChange={(e) => setResearchGoal(e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500"
                    placeholder="e.g. Evaluate usability, pricing fairness, and trust factors"
                  />
                </div>
              </div>

              {error && (
                <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs">
                  {error}
                </div>
              )}

              <div className="mt-6 flex items-center justify-between pt-4 border-t border-slate-100">
                <p className="text-[11px] text-slate-400">
                  Deterministic evaluation based on psychographic constraints & Faker profiles.
                </p>

                <button
                  onClick={handleRunSurvey}
                  disabled={loading}
                  className="px-5 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-xs font-bold transition shadow-sm flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                      <span>Executing Survey Across Cohort...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-current" />
                      <span>Execute Survey</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Results Section */}
            {surveyResult && (
              <div className="space-y-6">
                {/* Result Metrics */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <MetricCard
                    title="Product Fit Score"
                    value={`${surveyResult.product_fit_score?.toFixed(1) || 65} / 100`}
                    subtitle="Weighted synthetic satisfaction score"
                    icon={BarChart2}
                    iconColor="text-teal-600 bg-teal-50"
                  />
                  <MetricCard
                    title="Total Responses"
                    value={surveyResult.responses.length}
                    subtitle={`Captured from ${personas.length} personas`}
                    icon={Layers}
                    iconColor="text-blue-600 bg-blue-50"
                  />
                  <MetricCard
                    title="Adoption Barriers"
                    value={surveyResult.adoption_barriers?.length || 0}
                    subtitle="Key objections flagged"
                    icon={AlertTriangle}
                    iconColor="text-amber-600 bg-amber-50"
                  />
                </div>

                {/* Adoption Barriers Warning Box */}
                {surveyResult.adoption_barriers && surveyResult.adoption_barriers.length > 0 && (
                  <div className="bg-amber-50/70 border border-amber-200 p-4 rounded-xl">
                    <h3 className="text-xs font-bold text-amber-900 flex items-center gap-2 mb-2">
                      <AlertTriangle className="w-4 h-4 text-amber-600" />
                      Identified Adoption Barriers & Objections
                    </h3>
                    <ul className="space-y-1 text-xs text-amber-800">
                      {surveyResult.adoption_barriers.map((barrier, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-amber-600 font-bold">•</span>
                          <span>{barrier}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Survey Responses Table */}
                <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                  <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">Persona Survey Responses</h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Individual answers, scores, and cognitive reasoning per persona.
                      </p>
                    </div>
                    <button
                      onClick={() => router.push('/insights')}
                      className="px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold flex items-center gap-1.5 transition"
                    >
                      <span>Synthesize Insights</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 border-b border-slate-200 text-[11px] font-semibold text-slate-600 uppercase">
                        <tr>
                          <th className="py-3 px-4">Persona</th>
                          <th className="py-3 px-4">Question</th>
                          <th className="py-3 px-4">Answer</th>
                          <th className="py-3 px-4">Reasoning</th>
                          <th className="py-3 px-4 text-center">Score</th>
                          <th className="py-3 px-4">Sentiment</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 text-slate-700">
                        {surveyResult.responses.map((resp, idx) => (
                          <tr key={idx} className="hover:bg-slate-50/60 transition">
                            <td className="py-3 px-4 font-semibold text-slate-900 whitespace-nowrap">
                              {resp.persona_name}
                            </td>
                            <td className="py-3 px-4 max-w-xs text-slate-600">{resp.question}</td>
                            <td className="py-3 px-4 font-medium text-slate-900 whitespace-nowrap">{resp.answer}</td>
                            <td className="py-3 px-4 max-w-sm text-slate-500 leading-relaxed">{resp.reasoning}</td>
                            <td className="py-3 px-4 text-center">
                              <span className="font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-800">
                                {resp.score}
                              </span>
                            </td>
                            <td className="py-3 px-4 whitespace-nowrap">
                              <StatusBadge status={resp.sentiment || 'neutral'} size="sm" />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
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
