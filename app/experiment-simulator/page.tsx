'use client';

import React, { useState, useEffect } from 'react';
import { useAppStore } from '@/lib/store';
import { Navbar } from '@/components/Navbar';
import { MetricCard } from '@/components/MetricCard';
import { EmptyState } from '@/components/EmptyState';
import { runSimulationAPI } from '@/lib/api';
import { SimulationResult } from '@/lib/types';
import {
  Sliders,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  BarChart2,
  Zap,
  Info
} from 'lucide-react';

export default function ExperimentSimulatorPage() {
  const { personas, experiment, surveyResult, simulationResult, setSimulationResult } = useAppStore();

  const [pricingStrategy, setPricingStrategy] = useState<string>('Freemium / Free Trial');
  const [trustSignals, setTrustSignals] = useState<boolean>(true);
  const [onboardingFrictionReduction, setOnboardingFrictionReduction] = useState<number>(50);
  const [automationAdded, setAutomationAdded] = useState<boolean>(true);
  const [trialBonus, setTrialBonus] = useState<number>(15);
  const [guaranteeOffered, setGuaranteeOffered] = useState<boolean>(false);

  const [loading, setLoading] = useState<boolean>(false);

  const baseFit = surveyResult?.product_fit_score || 65.0;

  const runSimulation = async () => {
    setLoading(true);
    try {
      const res = await runSimulationAPI({
        baseline_fit: baseFit,
        pricing_strategy: pricingStrategy,
        trust_signals: trustSignals,
        onboarding_friction_reduction: onboardingFrictionReduction,
        automation_added: automationAdded,
        trial_bonus: trialBonus,
        guarantee_offered: guaranteeOffered,
      });
      setSimulationResult(res);
    } catch (e) {
      console.warn('Simulation failed', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, [pricingStrategy, trustSignals, onboardingFrictionReduction, automationAdded, trialBonus, guaranteeOffered, baseFit]);

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
      <Navbar
        title="Experiment & Scenario Simulator"
        subtitle="Simulate how product, pricing, and onboarding changes alter predicted adoption."
      />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
        {/* Top Disclaimer Badge */}
        <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between text-xs text-amber-900 shadow-sm">
          <div className="flex items-center gap-2 font-medium">
            <Info className="w-4 h-4 text-amber-600 flex-shrink-0" />
            <span>
              <strong className="font-bold">Simulated estimate</strong> — Not a production forecast. Predictions are model-derived synthetic approximations.
            </span>
          </div>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-200/60 text-amber-950 uppercase tracking-wider">
            Sandbox Mode
          </span>
        </div>

        {/* Simulator Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Controls Panel */}
          <div className="lg:col-span-6 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
            <div>
              <h2 className="text-base font-bold text-slate-900">Scenario Adjustments</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Modify product packaging, pricing models, and onboarding complexity.
              </p>
            </div>

            <div className="space-y-4">
              {/* Pricing Strategy */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">Pricing Strategy</label>
                <select
                  value={pricingStrategy}
                  onChange={(e) => setPricingStrategy(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 bg-white font-medium focus:outline-none focus:border-teal-500"
                >
                  <option value="Standard Paid">Standard Paid Tier ($29/mo)</option>
                  <option value="Freemium / Free Trial">Freemium / 14-Day Free Trial</option>
                  <option value="Discounted / Subsidy">Early-Adopter Discount (-25%)</option>
                  <option value="Enterprise Custom">Enterprise Custom Quoting</option>
                </select>
              </div>

              {/* Onboarding Slider */}
              <div>
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-semibold text-slate-700">Onboarding Friction Reduction</span>
                  <span className="font-bold text-teal-600">{onboardingFrictionReduction}%</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={100}
                  step={5}
                  value={onboardingFrictionReduction}
                  onChange={(e) => setOnboardingFrictionReduction(Number(e.target.value))}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-teal-600"
                />
                <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                  <span>Standard 7-Step Setup</span>
                  <span>1-Click Guided Wizard</span>
                </div>
              </div>

              {/* Trial Duration Bonus Slider */}
              <div>
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-semibold text-slate-700">Trial Duration / Discount Bonus</span>
                  <span className="font-bold text-teal-600">+{trialBonus}%</span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={50}
                  step={5}
                  value={trialBonus}
                  onChange={(e) => setTrialBonus(Number(e.target.value))}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-teal-600"
                />
              </div>

              {/* Checkbox Toggles */}
              <div className="pt-2 border-t border-slate-100 space-y-3">
                <label className="flex items-center gap-2.5 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={trustSignals}
                    onChange={(e) => setTrustSignals(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 w-4 h-4"
                  />
                  <span className="font-medium">Add SOC2 / Trust Badges & Verified Testimonials</span>
                </label>

                <label className="flex items-center gap-2.5 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={automationAdded}
                    onChange={(e) => setAutomationAdded(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 w-4 h-4"
                  />
                  <span className="font-medium">Bundle AI Automation Assistant & Templates</span>
                </label>

                <label className="flex items-center gap-2.5 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={guaranteeOffered}
                    onChange={(e) => setGuaranteeOffered(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 w-4 h-4"
                  />
                  <span className="font-medium">30-Day Money-Back Satisfaction Guarantee</span>
                </label>
              </div>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-6 space-y-6">
            {simulationResult && (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <MetricCard
                    title="Baseline Fit"
                    value={`${simulationResult.baseline_fit.toFixed(1)} / 100`}
                    subtitle="Initial cohort validation"
                    icon={BarChart2}
                    iconColor="text-slate-600 bg-slate-100"
                  />
                  <MetricCard
                    title="Simulated Fit"
                    value={`${simulationResult.simulated_fit.toFixed(1)} / 100`}
                    subtitle="Predicted new product fit"
                    delta={`${simulationResult.delta >= 0 ? '+' : ''}${simulationResult.delta.toFixed(1)} pts`}
                    deltaType={simulationResult.delta >= 0 ? 'positive' : 'negative'}
                    icon={TrendingUp}
                    iconColor="text-teal-600 bg-teal-50"
                  />
                  <MetricCard
                    title="Predicted Adoption"
                    value={`${simulationResult.predicted_adoption_rate.toFixed(1)}%`}
                    subtitle="Estimated cohort trial rate"
                    icon={Zap}
                    iconColor="text-emerald-600 bg-emerald-50"
                  />
                </div>

                {/* Visual Bar Comparison */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
                  <h3 className="text-sm font-bold text-slate-900">Baseline vs. Simulated Adoption Comparison</h3>

                  <div className="space-y-4 pt-2">
                    <div>
                      <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
                        <span>Baseline Product Fit</span>
                        <span>{simulationResult.baseline_fit.toFixed(1)} / 100</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-3.5 overflow-hidden">
                        <div
                          className="bg-slate-400 h-full rounded-full transition-all duration-300"
                          style={{ width: `${simulationResult.baseline_fit}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-xs font-semibold text-teal-800 mb-1">
                        <span>Simulated Product Fit (Experiment Configuration)</span>
                        <span className="font-bold text-teal-600">{simulationResult.simulated_fit.toFixed(1)} / 100</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-3.5 overflow-hidden">
                        <div
                          className="bg-teal-500 h-full rounded-full transition-all duration-300"
                          style={{ width: `${simulationResult.simulated_fit}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Factors Breakdown */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
                  <h3 className="text-sm font-bold text-slate-900">Simulated Factor Contribution</h3>
                  <div className="space-y-2">
                    {simulationResult.factors.map((f, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                        <span className="text-slate-700 font-medium">{f.factor}</span>
                        <span className="font-bold text-teal-700">{f.impact}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
