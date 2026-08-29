'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAppStore } from '@/lib/store';
import { Navbar } from '@/components/Navbar';
import { EmptyState } from '@/components/EmptyState';
import { StatusBadge } from '@/components/StatusBadge';
import { sendInterviewMessageAPI } from '@/lib/api';
import { Persona, InterviewMemory, InterviewMessage } from '@/lib/types';
import {
  MessageSquare,
  Send,
  User,
  Bot,
  BrainCircuit,
  HelpCircle,
  ShieldCheck,
  Sparkles,
  ChevronRight,
  AlertCircle
} from 'lucide-react';

function InterviewContent() {
  const searchParams = useSearchParams();
  const requestedPersona = searchParams ? searchParams.get('persona') : null;

  const { personas, experiment, interviewMemories, setInterviewMemories } = useAppStore();

  const [selectedPersonaIndex, setSelectedPersonaIndex] = useState<number>(0);
  const [inputQuestion, setInputQuestion] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Set initial selected persona if specified in query param
  useEffect(() => {
    if (requestedPersona && personas.length > 0) {
      const idx = personas.findIndex((p) => p.name.toLowerCase() === requestedPersona.toLowerCase());
      if (idx !== -1) setSelectedPersonaIndex(idx);
    }
  }, [requestedPersona, personas]);

  const activePersona: Persona | undefined = personas[selectedPersonaIndex];
  const activeMemory: InterviewMemory | undefined = activePersona
    ? interviewMemories[activePersona.name]
    : undefined;

  const currentHistory: InterviewMessage[] = activeMemory?.history || [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentHistory, loading]);

  const handleSendMessage = async (questionText?: string) => {
    const textToSend = (questionText || inputQuestion).trim();
    if (!textToSend || !activePersona) return;

    setInputQuestion('');
    setLoading(true);
    setError(null);

    try {
      const res = await sendInterviewMessageAPI({
        persona: activePersona,
        question: textToSend,
        memory_payload: activeMemory || null,
        experiment,
      });

      setInterviewMemories((prev) => ({
        ...prev,
        [activePersona.name]: res.memory,
      }));
    } catch (err: any) {
      setError(err.message || 'Failed to send question');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-slate-50">
      <Navbar
        title="Interactive 1-on-1 Interview"
        subtitle="Engage in live exploratory dialogues with memory-audited synthetic personas."
      />

      <main className="p-8 max-w-7xl mx-auto w-full flex-1 flex flex-col space-y-6">
        {personas.length === 0 ? (
          <EmptyState
            icon={MessageSquare}
            title="Personas Required"
            description="Generate personas in the Workspace before conducting interviews."
            actionHref="/"
            actionLabel="Generate Personas"
          />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
            {/* Left Column: Persona Profile & Memory Audit */}
            <div className="lg:col-span-4 space-y-5">
              {/* Persona Selector */}
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Select Persona to Interview
                  </label>
                  <select
                    value={selectedPersonaIndex}
                    onChange={(e) => setSelectedPersonaIndex(Number(e.target.value))}
                    className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 bg-white font-medium focus:outline-none focus:border-teal-500"
                  >
                    {personas.map((p, idx) => (
                      <option key={idx} value={idx}>
                        {p.name} ({p.occupation})
                      </option>
                    ))}
                  </select>
                </div>

                {activePersona && (
                  <div className="pt-3 border-t border-slate-100 space-y-3 text-xs">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-800 font-bold flex items-center justify-center text-sm border border-teal-200">
                        {activePersona.name.charAt(0)}
                      </div>
                      <div>
                        <h4 className="font-bold text-slate-900">{activePersona.name}</h4>
                        <p className="text-[11px] text-slate-500">{activePersona.occupation} • {activePersona.age} y/o</p>
                      </div>
                    </div>

                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-[11px] text-slate-600 space-y-1">
                      <p><span className="font-semibold text-slate-800">Tech Usage:</span> {activePersona.technology_usage}</p>
                      <p><span className="font-semibold text-slate-800">Buying Style:</span> {activePersona.buying_behavior}</p>
                      <p className="line-clamp-2 mt-1 italic">&quot;{activePersona.bio}&quot;</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Memory & Consistency Audit Card */}
              {activeMemory && (
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-3 text-xs">
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-slate-900 flex items-center gap-1.5 text-xs">
                      <BrainCircuit className="w-3.5 h-3.5 text-teal-600" />
                      Conversation Memory
                    </h3>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-teal-50 text-teal-700 border border-teal-200">
                      Score: {activeMemory.consistency_score}%
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-500 leading-relaxed">
                    {activeMemory.conversation_summary || 'No opinion checkpoints logged yet.'}
                  </p>

                  {activeMemory.emotional_state && (
                    <div className="flex items-center gap-2 pt-2 border-t border-slate-100 text-[11px]">
                      <span className="text-slate-500 font-medium">Current Emotional State:</span>
                      <StatusBadge status={activeMemory.emotional_state} size="sm" />
                    </div>
                  )}

                  {activeMemory.contradictions && activeMemory.contradictions.length > 0 && (
                    <div className="p-2.5 bg-rose-50 border border-rose-100 rounded-lg text-rose-700 text-[11px]">
                      <span className="font-bold block">Contradiction Warning:</span>
                      {activeMemory.contradictions.join(', ')}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Right Column: Chat Dialogue Area */}
            <div className="lg:col-span-8 bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col h-[640px] overflow-hidden">
              {/* Chat Header */}
              <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                  <span className="font-bold text-xs text-slate-900">
                    Interviewing {activePersona?.name || 'Persona'}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
                  Gemini LLM with Persona-Anchored Memory
                </div>
              </div>

              {/* Chat Messages */}
              <div className="flex-1 p-6 overflow-y-auto space-y-4">
                {currentHistory.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 p-8 space-y-3">
                    <MessageSquare className="w-8 h-8 text-slate-300" />
                    <p className="text-xs font-medium text-slate-600">
                      No messages yet. Ask a question to start the interview with {activePersona?.name}.
                    </p>
                    <div className="space-y-1.5 w-full max-w-sm pt-2">
                      <p className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Suggested starter questions:</p>
                      {[
                        'What is your biggest daily blocker in your workflow?',
                        'How would you evaluate this product before paying?',
                        'What would make you hesitate to adopt this solution?',
                      ].map((prompt, i) => (
                        <button
                          key={i}
                          onClick={() => handleSendMessage(prompt)}
                          className="w-full p-2 rounded-lg bg-slate-50 border border-slate-200 hover:bg-teal-50 hover:border-teal-200 text-left text-[11px] text-slate-700 transition"
                        >
                          &quot;{prompt}&quot;
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  currentHistory.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      {msg.role === 'persona' && (
                        <div className="w-8 h-8 rounded-full bg-teal-100 text-teal-800 font-bold flex-shrink-0 flex items-center justify-center text-xs border border-teal-200 mt-1">
                          {activePersona?.name.charAt(0)}
                        </div>
                      )}

                      <div
                        className={`max-w-md p-3.5 rounded-xl text-xs leading-relaxed ${
                          msg.role === 'user'
                            ? 'bg-teal-600 text-white rounded-tr-none'
                            : 'bg-slate-100 text-slate-800 rounded-tl-none border border-slate-200'
                        }`}
                      >
                        <p>{msg.message}</p>
                        {msg.emotional_state && (
                          <div className="mt-2 pt-1.5 border-t border-slate-200/60 flex items-center justify-between text-[10px] text-slate-500">
                            <span>Tone: {msg.emotional_state}</span>
                            {msg.topic && <span>Topic: {msg.topic}</span>}
                          </div>
                        )}
                      </div>

                      {msg.role === 'user' && (
                        <div className="w-8 h-8 rounded-full bg-slate-900 text-white font-bold flex-shrink-0 flex items-center justify-center text-xs mt-1">
                          <User className="w-4 h-4" />
                        </div>
                      )}
                    </div>
                  ))
                )}

                {loading && (
                  <div className="flex gap-3 justify-start">
                    <div className="w-8 h-8 rounded-full bg-teal-100 text-teal-800 font-bold flex-shrink-0 flex items-center justify-center text-xs border border-teal-200">
                      {activePersona?.name.charAt(0)}
                    </div>
                    <div className="bg-slate-100 text-slate-500 p-3 rounded-xl text-xs flex items-center gap-2 border border-slate-200">
                      <span className="w-3.5 h-3.5 border-2 border-teal-600 border-t-transparent rounded-full animate-spin"></span>
                      <span>{activePersona?.name} is thinking...</span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Suggested Follow-Ups */}
              {activeMemory?.follow_up_questions && activeMemory.follow_up_questions.length > 0 && (
                <div className="px-6 py-2 bg-slate-50 border-t border-slate-100 flex items-center gap-2 overflow-x-auto text-[11px]">
                  <span className="text-slate-400 font-semibold flex-shrink-0">Follow-up:</span>
                  {activeMemory.follow_up_questions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(q)}
                      className="px-2.5 py-1 rounded-full bg-white border border-slate-200 hover:border-teal-400 hover:text-teal-700 text-slate-600 whitespace-nowrap transition"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}

              {/* Chat Input */}
              <div className="p-4 border-t border-slate-200 bg-white">
                {error && (
                  <div className="mb-2 p-2 bg-rose-50 border border-rose-200 rounded text-rose-700 text-xs">
                    {error}
                  </div>
                )}
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                  }}
                  className="flex gap-2"
                >
                  <input
                    type="text"
                    value={inputQuestion}
                    onChange={(e) => setInputQuestion(e.target.value)}
                    placeholder={`Ask ${activePersona?.name || 'persona'} a question about their habits, pricing, or needs...`}
                    className="flex-1 px-4 py-2.5 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 transition"
                  />
                  <button
                    type="submit"
                    disabled={loading || !inputQuestion.trim()}
                    className="px-4 py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-xs font-bold transition flex items-center gap-1.5"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Send</span>
                  </button>
                </form>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function InterviewPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 flex items-center justify-center p-12 text-xs text-slate-500">
          Loading interview interface...
        </div>
      }
    >
      <InterviewContent />
    </Suspense>
  );
}
