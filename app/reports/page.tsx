'use client';

import React, { useState, useEffect } from 'react';
import { useAppStore } from '@/lib/store';
import { Navbar } from '@/components/Navbar';
import { MetricCard } from '@/components/MetricCard';
import { EmptyState } from '@/components/EmptyState';
import { fetchReportsAPI } from '@/lib/api';
import { ConsultantReport } from '@/lib/types';
import {
  FileText,
  Download,
  Printer,
  Sparkles,
  CheckCircle2,
  Share2,
  Copy,
  Check,
  Compass
} from 'lucide-react';

export default function ReportsPage() {
  const {
    personas,
    experiment,
    surveyResult,
    interviewMemories,
    insights,
    focusGroupTranscript,
    report,
    setReport,
  } = useAppStore();

  const [loading, setLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateReport = async () => {
    if (personas.length === 0) {
      setError('Please generate personas before producing an intelligence report.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const interviewRows = Object.values(interviewMemories).flatMap((m) => m.history || []);
      const res = await fetchReportsAPI({
        experiment,
        personas,
        survey_results: surveyResult,
        interview_rows: interviewRows,
        insights,
        focus_group: focusGroupTranscript,
      });
      setReport(res);
    } catch (err: any) {
      setError(err.message || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (personas.length > 0 && !report) {
      handleGenerateReport();
    }
  }, [personas]);

  const handleCopy = () => {
    if (report?.markdown) {
      navigator.clipboard.writeText(report.markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (report?.markdown) {
      const blob = new Blob([report.markdown], { type: 'text/markdown;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${experiment.product_name || 'research'}_report.md`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
      <Navbar
        title="Executive Intelligence Reports"
        subtitle="Comprehensive product discovery and launch readiness dossier."
      />

      <main className="p-8 max-w-7xl mx-auto w-full space-y-8">
        {personas.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="Personas Required"
            description="Generate personas in the Workspace to produce a synthesized intelligence report."
            actionHref="/"
            actionLabel="Generate Personas"
          />
        ) : (
          <>
            {/* Action Bar */}
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <h2 className="text-base font-bold text-slate-900">Synthetic Research Dossier</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Compiled from persona generation, survey results, 1-on-1 interviews, and action planning.
                </p>
              </div>

              <div className="flex items-center gap-2">
                {report && (
                  <>
                    <button
                      onClick={handleCopy}
                      className="px-3.5 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-1.5 transition"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copied ? 'Copied' : 'Copy Markdown'}</span>
                    </button>

                    <button
                      onClick={handleDownload}
                      className="px-3.5 py-2 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold flex items-center gap-1.5 transition"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download .md</span>
                    </button>
                  </>
                )}

                <button
                  onClick={handleGenerateReport}
                  disabled={loading}
                  className="px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-xs font-bold transition flex items-center gap-1.5 shadow-sm"
                >
                  {loading ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                      <span>Compiling Report...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{report ? 'Re-Generate Report' : 'Generate Full Report'}</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs">
                {error}
              </div>
            )}

            {/* Report Document Viewer */}
            {report?.markdown && (
              <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm space-y-6 max-w-4xl mx-auto">
                <div className="border-b border-slate-200 pb-4">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-teal-600 block">
                    AI Research Studio • Executive Report
                  </span>
                  <h1 className="text-xl font-bold text-slate-900 mt-1">
                    {experiment.product_name || 'Product'} Intelligence Dossier
                  </h1>
                  <p className="text-xs text-slate-500 mt-1">
                    Experiment: {experiment.experiment_name} | Generated for {personas.length} synthetic personas
                  </p>
                </div>

                <div className="prose prose-slate max-w-none text-xs text-slate-800 space-y-4 whitespace-pre-wrap font-mono leading-relaxed bg-slate-50/70 p-6 rounded-xl border border-slate-200">
                  {report.markdown}
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
