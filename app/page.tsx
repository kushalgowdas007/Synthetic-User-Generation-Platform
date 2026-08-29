'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAppStore } from '@/lib/store';
import { Navbar } from '@/components/Navbar';
import { MetricCard } from '@/components/MetricCard';
import { generatePersonasAPI } from '@/lib/api';
import {
  Sparkles,
  Users,
  Sliders,
  Layers,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Clock,
  Briefcase
} from 'lucide-react';

export default function WorkspacePage() {
  const router = useRouter();
  const { experiment, setExperiment, personas, setPersonas, surveyResult, insights, actions } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sourceInfo, setSourceInfo] = useState<string | null>(null);

  const handleInputChange = (field: keyof typeof experiment, value: any) => {
    setExperiment((prev) => ({ ...prev, [field]: value }));
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!experiment.product_name.trim()) {
      setError('Please provide a Product Name.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await generatePersonasAPI(experiment);
      setPersonas(res.personas);
      setSourceInfo(`Cohort generated via ${res.source === 'gemini' ? 'Gemini 2.5 LLM' : 'Faker Synthetic Generator'}`);
    } catch (err: any) {
      setError(err.message || 'Failed to generate personas');
    } finally {
      setLoading(false);
    }
  };

  const loadDemoBrief = () => {
    setExperiment({
      experiment_name: 'DevFlow AI Launch Validation',
      product_name: 'DevFlow AI',
      description: 'Intelligent code review assistant and sprint velocity accelerator for modern engineering teams.',
      target_audience: 'Senior Full-Stack Engineers, Tech Leads, Engineering Managers',
      research_objective: 'Evaluate willingness to pay $29/mo, onboarding friction, and security concerns.',
      industry: 'Developer Tools / Enterprise SaaS',
      simulation_type: 'Product Adoption & Pricing',
      persona_count: 5,
      age: '25-45',
      gender: 'Diverse Cohort',
      profession: 'Software Engineering & Tech Leadership',
      location: 'Global / Tech Hubs',
      interests: 'Clean Code, Productivity, Automation, CI/CD pipelines',
    });
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
      <Navbar
        title="Home / Research Workspace"
        subtitle="Configure research parameters and synthesize high-fidelity user personas."
      />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
        {/* Metric Overview Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Generated Personas"
            value={personas.length}
            subtitle={personas.length > 0 ? 'Active research cohort' : 'No personas yet'}
            icon={Users}
          />
          <MetricCard
            title="Survey Status"
            value={surveyResult ? 'Completed' : 'Pending'}
            subtitle={surveyResult ? `${surveyResult.responses.length} responses recorded` : 'Ready to run'}
            icon={Layers}
            iconColor="text-blue-600 bg-blue-50"
          />
          <MetricCard
            title="Extracted Insights"
            value={insights ? `${insights.structured_insights?.length || 0}` : '0'}
            subtitle={insights ? 'Evidence-backed clusters' : 'Synthesize after survey'}
            icon={Sparkles}
            iconColor="text-purple-600 bg-purple-50"
          />
          <MetricCard
            title="Product Decisions"
            value={actions.length}
            subtitle={actions.length > 0 ? 'Prioritized actions' : 'Generated in Action Center'}
            icon={Briefcase}
            iconColor="text-emerald-600 bg-emerald-50"
          />
        </div>

        {/* Main Grid: Form + Cohort Preview */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left: Input Form */}
          <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
              <div>
                <h2 className="text-base font-bold text-slate-900">Research Brief & Cohort Configuration</h2>
                <p className="text-xs text-slate-500 mt-0.5">Define your product scenario and demographic target.</p>
              </div>
              <button
                type="button"
                onClick={loadDemoBrief}
                className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-teal-200 bg-teal-50 text-teal-700 hover:bg-teal-100 transition flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5" />
                Load Sample Brief
              </button>
            </div>

            <form onSubmit={handleGenerate} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Experiment Name</label>
                  <input
                    type="text"
                    value={experiment.experiment_name}
                    onChange={(e) => handleInputChange('experiment_name', e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition"
                    placeholder="e.g. Q3 Pricing Validation"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Product Name *</label>
                  <input
                    type="text"
                    required
                    value={experiment.product_name}
                    onChange={(e) => handleInputChange('product_name', e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition"
                    placeholder="e.g. TaskFlow AI"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Product Description</label>
                <textarea
                  rows={2}
                  value={experiment.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition"
                  placeholder="Explain what the product does and the core value proposition..."
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Target Audience</label>
                  <input
                    type="text"
                    value={experiment.target_audience}
                    onChange={(e) => handleInputChange('target_audience', e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition"
                    placeholder="e.g. B2B Engineering Managers"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Research Objective</label>
                  <input
                    type="text"
                    value={experiment.research_objective}
                    onChange={(e) => handleInputChange('research_objective', e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition"
                    placeholder="e.g. Test price sensitivity and trial barriers"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Industry</label>
                  <input
                    type="text"
                    value={experiment.industry}
                    onChange={(e) => handleInputChange('industry', e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition"
                    placeholder="e.g. SaaS / FinTech"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Simulation Type</label>
                  <input
                    type="text"
                    value={experiment.simulation_type}
                    onChange={(e) => handleInputChange('simulation_type', e.target.value)}
                    className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition"
                    placeholder="e.g. Product Adoption"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Persona Count: <span className="font-bold text-teal-600">{experiment.persona_count}</span>
                  </label>
                  <input
                    type="range"
                    min={2}
                    max={8}
                    value={experiment.persona_count}
                    onChange={(e) => handleInputChange('persona_count', parseInt(e.target.value))}
                    className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-teal-600 mt-2"
                  />
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100">
                <h3 className="text-xs font-bold text-slate-800 mb-2 uppercase tracking-wider">Demographics & Profile Constraints</h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">Age Range</label>
                    <input
                      type="text"
                      value={experiment.age}
                      onChange={(e) => handleInputChange('age', e.target.value)}
                      className="w-full px-2.5 py-1.5 text-xs rounded border border-slate-200 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">Gender</label>
                    <input
                      type="text"
                      value={experiment.gender}
                      onChange={(e) => handleInputChange('gender', e.target.value)}
                      className="w-full px-2.5 py-1.5 text-xs rounded border border-slate-200 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">Profession</label>
                    <input
                      type="text"
                      value={experiment.profession}
                      onChange={(e) => handleInputChange('profession', e.target.value)}
                      className="w-full px-2.5 py-1.5 text-xs rounded border border-slate-200 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-slate-600 mb-1">Location</label>
                    <input
                      type="text"
                      value={experiment.location}
                      onChange={(e) => handleInputChange('location', e.target.value)}
                      className="w-full px-2.5 py-1.5 text-xs rounded border border-slate-200 focus:outline-none focus:border-teal-500"
                    />
                  </div>
                </div>
              </div>

              {error && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="pt-2 flex items-center justify-between">
                <div className="text-[11px] text-slate-400 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                  Server-side Gemini + Deterministic Faker Enrichment
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="px-5 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-xs font-bold transition shadow-sm flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                      <span>Generating Synthetic Cohort...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>Generate Personas</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Right: Active Cohort Status */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
              <h2 className="text-base font-bold text-slate-900 mb-1">Active Research Cohort</h2>
              <p className="text-xs text-slate-500 mb-4">Live personas available for survey execution and interviews.</p>

              {personas.length === 0 ? (
                <div className="p-8 text-center border-2 border-dashed border-slate-200 rounded-xl bg-slate-50/50">
                  <Users className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <p className="text-xs font-semibold text-slate-700">No personas generated yet</p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Fill out the research brief and click &quot;Generate Personas&quot; to synthesize your cohort.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {sourceInfo && (
                    <div className="p-2.5 bg-teal-50 border border-teal-100 rounded-lg text-teal-800 text-[11px] flex items-center gap-2 font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
                      <span>{sourceInfo}</span>
                    </div>
                  )}

                  <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                    {personas.map((p, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between text-xs hover:bg-slate-100 transition"
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="w-7 h-7 rounded-full bg-teal-200 text-teal-800 font-bold flex items-center justify-center text-xs">
                            {p.name.charAt(0)}
                          </div>
                          <div>
                            <span className="font-semibold text-slate-900 block">{p.name}</span>
                            <span className="text-[10px] text-slate-500">{p.occupation} • {p.age} y/o</span>
                          </div>
                        </div>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-white border border-slate-200 text-teal-700">
                          Score: {p.quality_score || 90}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="pt-2">
                    <button
                      onClick={() => router.push('/personas')}
                      className="w-full py-2.5 px-4 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold transition flex items-center justify-center gap-2"
                    >
                      <span>Explore Persona Lab</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Workflow Quick Links */}
            <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-6 text-white shadow-sm space-y-3">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-teal-400" />
                Recommended Next Step
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                {personas.length === 0
                  ? 'Start by generating synthetic personas from your brief.'
                  : !surveyResult
                  ? 'Run a simulated survey to evaluate product adoption and pricing feedback across your cohort.'
                  : 'Proceed to Insights to synthesize evidence-backed strategic recommendations.'}
              </p>

              {personas.length > 0 && !surveyResult && (
                <button
                  onClick={() => router.push('/survey')}
                  className="mt-2 inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 text-xs font-bold transition"
                >
                  <span>Run Cohort Survey</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
